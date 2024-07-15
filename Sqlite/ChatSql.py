"""
Des 对话，聊天记录和面具的本地数据库
@Author MisakaW
Time 2024/6/29
"""
from sqlalchemy import create_engine, DateTime, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column
from enum import Enum as BaseEnum
from datetime import datetime
from Logging import app_logger

Base = declarative_base()


# =============================================表的定义=============================================

class SenderType(BaseEnum):
    """
    信息发送人枚举体
    """
    USER = 0
    GPT = 1


class SendType(BaseEnum):
    """
    信息发送类型枚举体
    """
    TEXT = 0
    IMAGE = 1
    AUDIO = 2


class Mask(Base):
    """
    面具
    """
    __tablename__ = 'mask'  # 表名修改为'mask'
    mask_id = Column(Integer, primary_key=True, autoincrement=True)
    mask_name = Column(String(50), unique=True)
    mask_describe = Column(String(500))


class Dialogue(Base):
    """
    对话
    """
    __tablename__ = 'dialogue'
    dialogue_name = Column(String(50), primary_key=True)
    mask_id = Column(Integer, ForeignKey('mask.mask_id'))  # 外键关联到Mask表的mask_id
    mask = relationship("Mask", back_populates="dialogues")  # 关联到Mask，并设置反向引用
    messages = relationship("Message", back_populates="dialogue")  # 关联到Message，并设置反向引用

    # 反向引用到Mask，表示一个Mask可以有多个Dialogue
    @declared_attr
    def mask(cls):
        return relationship("Mask", foreign_keys=[cls.mask_id])


class Message(Base):
    """
    聊天信息
    """
    __tablename__ = 'message'  # 表名修改为'message'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(Enum(SenderType, name="sender_enum"))
    send_time = Column(DateTime)
    send_type = Column(Enum(SendType, name="send_type_enum"))
    send_info = Column(String(2000))
    send_succeed = Column(Boolean)
    dialogue_name = Column(String(50), ForeignKey('dialogue.dialogue_name'))  # 外键关联到Dialogue表的dialogue_name
    dialogue = relationship("Dialogue", back_populates="messages")  # 关联到Dialogue，并设置反向引用


# =============================================数据库封装=============================================

class ChatSql:
    def __init__(self):
        """
        初始化数据库连接和会话
        """
        # =============================================基础设置start=============================================
        try:
            engine = create_engine('sqlite:///chat.db')
            Base.metadata.create_all(engine)
            self.DB_session = sessionmaker(bind=engine)
            self.add_mask("default")
        except Exception as e:
            app_logger.info(str(e))

        # =============================================基础设置end=============================================

    def create_dialogue(self, name: str, mask_name: str = ""):
        """
        创建对话
        :param name: 对话名称
        :param mask_name: 面具名称，可以没有
        """
        try:
            with self.DB_session() as session:
                mask = session.query(Mask).filter_by(mask_name=mask_name).first()
                if mask_name == "" or not mask:
                    mask = session.query(Mask).filter_by(mask_name="default").first()
                if session.query(Dialogue).filter_by(dialogue_name=name): # 已经出现
                    return
                dialogue = Dialogue(dialogue_name=name, mask_id=mask.mask_id)
                session.add(dialogue)
                session.flush()
                session.commit()
        except Exception as e:
            app_logger.info(str(e))
            print(str(e))

    def add_message(self, dialogue_name: str, sender: SenderType, send_type: SendType,
                    send_info: str, send_succeed: bool, send_time: DateTime = datetime.now()):
        """
        添加消息
        :param dialogue_name: 对话名称
        :param sender: 发送者类型
        :param send_time: 发送时间
        :param send_type: 发送类型
        :param send_info: 发送信息
        :param send_succeed: 发送是否成功
        """
        try:
            with self.DB_session() as session:
                dialogue = session.query(Dialogue).filter_by(dialogue_name=dialogue_name).first()
                if not dialogue:
                    print(f"Dialogue with name {dialogue_name} not found")
                message = Message(dialogue=dialogue, sender=sender, send_time=send_time, send_type=send_type,
                                  send_info=send_info, send_succeed=send_succeed)
                session.add(message)
                session.commit()
        except Exception as e:
            app_logger.info(str(e))

    def update_message(self, message_id: int, new_send_info: str):
        """
        更新消息
        :param message_id: 消息ID
        :param new_send_info: 新的发送信息
        """
        try:
            with self.DB_session() as session:
                message = session.query(Message).get(message_id)
                if message:
                    message.send_info = new_send_info
                    session.commit()
                else:
                    print(f"Message with id {message_id} not found")
        except Exception as e:
            app_logger.info(str(e))

    def delete_message(self, message_id: int):
        """
        删除消息
        :param message_id: 消息ID
        """
        try:
            with self.DB_session() as session:
                message = session.query(Message).get(message_id)
                if message:
                    session.delete(message)
                    session.commit()
                else:
                    print(f"Message with id {message_id} not found")
        except Exception as e:
            app_logger.info(str(e))

    def get_dialogue(self, dialogue_name: str) -> None:
        """
        根据名称获取对话
        :param dialogue_name: 对话名称
        """
        try:
            with self.DB_session() as session:
                return session.query(Dialogue).filter_by(dialogue_name=dialogue_name).first()
        except Exception as e:
            app_logger.info(str(e))

    def get_messages(self, dialogue_name: str) -> list:
        """
        根据对话名称获取消息
        :param dialogue_name: 对话名称
        :return: 消息列表，如果未找到相关对话则返回空列表
        """
        try:
            with self.DB_session() as session:
                dialogue = session.query(Dialogue).filter_by(dialogue_name=dialogue_name).first()
                if dialogue:
                    return dialogue.messages
                else:
                    return []
        except Exception as e:
            app_logger.info(str(e))

    def add_mask(self, mask_name: str, mask_describe: str = ""):
        """
        增加新的面具
        :param mask_name: 面具名称
        :param mask_describe: 面具描述
        """
        try:
            with self.DB_session() as session:
                new_mask = Mask(mask_name=mask_name, mask_describe=mask_describe)
                session.add(new_mask)
                session.commit()
        except Exception as e:
            app_logger.info(str(e))

    def get_mask(self, mask_name: str):
        """
        根据名称查找面具
        :param mask_name: 面具名称
        :return: 面具对象，如果未找到则返回 None
        """
        try:
            with self.DB_session() as session:
                return session.query(Mask).filter_by(mask_name=mask_name).first()
        except Exception as e:
            app_logger.info(str(e))

    def delete_mask(self, mask_name: str):
        """
        根据名称删除面具
        :param mask_name: 面具名称
        """
        try:
            with self.DB_session() as session:
                mask = self.get_mask(mask_name)
                if mask:
                    session.delete(mask)
                    session.commit()
                else:
                    print(f"Mask with name {mask_name} not found")
        except Exception as e:
            app_logger.info(str(e))

    def __format__(self, format_spec: str) -> str:
        """
        格式化输出
        """
        try:
            with self.DB_session() as session:
                if format_spec == "dialogues":
                    dialogues = session.query(Dialogue).all()
                    return "\n".join(
                        [f"对话名: {dialogue.dialogue_name}, 面具id: {dialogue.mask_id}" for dialogue in dialogues])
                elif format_spec == "masks":
                    masks = session.query(Mask).all()
                    return "\n".join(
                        [f"面具id: {mask.mask_id}, 面具名: {mask.mask_name}, 面具描述: {mask.mask_describe}" for mask in
                         masks])
                elif "messages" in format_spec:  # e.g. "messages Dialogue1 5"
                    target_format = format_spec.split(' ')
                    if len(target_format) < 2:
                        return "Miss parameters"
                    update_num = int(target_format[-1]) if len(target_format) >= 2 else 5
                    dialogue_name = target_format[1]
                    dialogue = session.query(Dialogue).filter_by(dialogue_name=dialogue_name).first()
                    if dialogue:
                        messages = dialogue.messages
                        sorted_messages = sorted(messages, key=lambda x: x.id, reverse=True)
                        print_messages = sorted_messages[:update_num]
                        return "\n".join([
                                             f"信息id: {message.id}, 发送者: {message.sender.name}, 发送时间: {message.send_time}, 发送类型: {message.send_type.name}, 发送内容: {message.send_info}, 发送是否成功: {message.send_succeed}"
                                             for message in print_messages])
                    else:
                        return f"未找到 {dialogue_name} 这个对话"
                else:
                    app_logger.info("Unknown format specifier")
        except Exception as e:
            app_logger.info(str(e))
            return str(e)


if __name__ == '__main__':
    sql = ChatSql()
    sql.add_mask("Mask1", mask_describe="test mask")
    sql.create_dialogue("Dialogue1", "Mask1")
    for i in range(30):
        sql.add_message("Dialogue1", SenderType.USER, SendType.TEXT, str(i), True)
    dialogue = sql.get_dialogue("Dialogue1")
    messages = sql.get_messages("Dialogue1")
    print(format(sql, "dialogues"))
    print(format(sql, "masks"))
    print(format(sql, "messages Dialogue1 6"))
