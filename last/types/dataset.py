from typing import List, Dict, Union, Optional, TypeVar, Tuple
from dataclasses import dataclass
from .base import Record, Statistics, BaseManager
from .public import RiskDimension, ReturnCode, ID
from datetime import datetime
from pydantic import HttpUrl, Field, validator
import csv
from enum import Enum

DatasetTyping = TypeVar("DatasetTyping", bound="Dataset")


class MessageRole(str, Enum):
    System = "System"
    AI = "AI"
    Human = "Human"
    Chat = "Chat"


class Message(Record):
    role: MessageRole
    content: str


class Annotation(Record):
    pass


class QARecord(Record):
    predecessor_uid: Optional[str] = None  # 关联上一条Message记录的id, 用于多轮对话，目前不启用
    successor_uid: Optional[str] = None  # 关联下一条Message记录的id, 用于多轮对话，目前不启用
    question: Message
    answer: Optional[Message] = None
    critic: Optional[Message] = None  # critic模型对该条QARecord的回复
    annotation: Optional[Annotation] = None  # QARecord对应的人工标注结果


class Dataset(Record, BaseManager):
    name: Optional[str] = Field(default=None)  # 模型名称
    focused_risks: Optional[List[RiskDimension]] = Field(default=None)  # 风险详情
    url: Optional[HttpUrl] = None  # 文件导出url
    file: Optional[str] = None  # 文件本地path
    volume: Optional[str] = Field(default="0.0GB")  # 数据集大小GB
    used_by: Optional[int] = Field(default=0)  # 使用次数
    qa_num: Optional[int] = Field(default=0, init=False)  # 对话条数
    word_cnt: Optional[int] = Field(default=0, init=False)  # 语料字数

    qa_records: Optional[
        Dict[str, QARecord]
    ] = None  # key是每条QARecord的唯一id, 也是Dataset类中的实际内容存储

    conversation_start_id: Optional[
        List[str]
    ] = None  # 每段对话的起始QARecord id, 为了多轮对话，目前暂时不启用
    current_conversation_index: Optional[int] = Field(default=0, init=False)  # 供迭代器使用
    current_qa_record_id: Optional[int] = Field(default=0, init=False)  # 供迭代器使用

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.file is not None:  # 根据传入的file path，新建Dataset对象
            self.qa_records = Dataset.upload(self.file)
        elif self.qa_records is not None:  # 根据传入的file path，新建Dataset对象
            pass
        else:
            raise ValueError("Input parameter cannot be empty")

        self.fill_attributes(self.qa_records)

    @staticmethod
    def upload(file_path: str) -> Tuple[Dict[str, QARecord], List[str]]:
        # TODO 注释掉的部分是为了给多轮对话准备的，目前还没有经过测试，故不写
        # 通过上传文件创建数据集
        qa_records = {}
        # predecessor_uid = None # 关联上一条Message记录的id
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                self_uid = ID()
                question = Message(role=MessageRole.Human, content=row["question"])
                correct_ans = Message(role=MessageRole.AI, content=row["correct_ans"])
                # successor_uid = ID() # 提前安排好下一条数据的ID
                qa_records[self_uid] = QARecord(
                    predecessor_uid=None,
                    successor_uid=None,
                    question=question,
                    answer=correct_ans,
                )
                # predecessor_uid = self_uid
        return qa_records

    # TODO 根据qa_records填充其他属性, 现在是mock的
    def fill_attributes(self, qa_records: Dict[str, QARecord]) -> None:
        self.conversation_start_id = list(self.qa_records.keys())
        self.qa_num = len(qa_records)
        self.word_cnt = 100000  # TODO 总语料字数的获取函数暂时还没有写
        self.volume = "10.6GB"
        self.focused_risks = [
            RiskDimension(name="国家安全", downlevel_risk_name=["颠覆国家政权", "宣扬恐怖主义", "挑拨民族对立"]),
            RiskDimension(level=2, name="颠覆国家政权", downlevel_risk_name=["反政府组织", "暴力政治活动", "革命行动"]),
            RiskDimension(level=2, name="宣扬恐怖主义", downlevel_risk_name=["恐怖组织宣传", "暴力恐吓手段", "恐怖袭击策划"]),
            RiskDimension(level=2, name="挑拨民族对立", downlevel_risk_name=["种族仇恨煽动", "民族主义煽动", "社会分裂策略"]),
        ]  # TODO 单独写函数获取focused_risks

    @property
    def length(self):
        return len(self.qa_records)

    def __iter__(self):
        self.current_conversation_index = 0
        self.current_qa_record_id = self.conversation_start_id[0]
        return self

    def __next__(self) -> QARecord:
        # 每次迭代时，只输出一条QARecord消息，
        # 第一次迭代的时候，输出第一个conversation里面的第一条消息
        # 下次迭代时，输出第二条消息
        # 如果当前conversation已经迭代完毕（即successor_uid为None），则输出第二个conversation里面的第一条消息
        # 直到所有的conversation输出完毕
        if self.current_conversation_index >= len(self.qa_records):
            raise StopIteration

        qa_record = self.qa_records[self.current_qa_record_id]

        if qa_record.successor_uid is None:
            self.current_conversation_index += 1
            if self.current_conversation_index < len(self.conversation_start_id):
                self.current_qa_record_id = self.conversation_start_id[
                    self.current_conversation_index
                ]
        else:
            self.current_qa_record_id = qa_record.successor_uid
        return qa_record

    @staticmethod
    def edit(uid, conf: DatasetTyping) -> ReturnCode:  # 编辑数据集信息，返回状态码
        # 根据提供的id获取记录
        records = Dataset.get_records([uid])
        if not records:
            return ReturnCode.NOT_FOUND
        record = records[0]  # 获取唯一的记录
        # 更新记录的相关字段
        record.name = conf.name
        record.dimensions = conf.dimensions
        record.url = conf.url
        record.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 更新记录到数据库，这里假设有一个名为update_record的静态方法来更新数据库
        Dataset.update_record(record)

        return ReturnCode.SUCCESS

    @staticmethod
    def fetch(url: HttpUrl):
        # 通过访问url创建数据集
        pass

    @classmethod
    def create_from_file(cls, file_path: str) -> Union[DatasetTyping, str]:
        dataset = cls(file=file_path)
        return dataset
