# _*_ coding:utf-8 _*_

from kernel_nlp.kernel_nlp_config import KernelNLPConfig

class StateMachine:
    def __init__(self):
        self.handlers = {}  # 状态转移函数字典
        self.startState = None  # 初始状态
        self.endStates = []  # 最终状态集合

    # 参数name为状态名,handler为状态转移函数,end_state表明是否为最终状态
    def add_state(self, name, handler, end_state=0):
        name = name.upper()  # 转换为大写
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_start(self, name):
        self.startState = name.upper()

    def run(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise Exception("启动前需设置初始状态")
        if not self.endStates:
            raise Exception("必须有终止状态")

        # 从Start状态开始进行处理
        index = 0
        length = len(cargo)
        while True:
            (newState, index) = handler(cargo, index)  # 经过状态转移函数变换到新状态
            if index >= length:
                return index, newState
            if newState.upper() in self.endStates:  # 如果跳到终止状态,则打印状态并结束循环
                return index, newState
            else:  # 否则将转移函数切换为新状态下的转移函数
                handler = self.handlers[newState.upper()]


class Transition(object):
    """状态转移函数"""
    @staticmethod
    def _construct_model():
        m = StateMachine()
        m.add_state("Start", Transition.start_transitions)  # 添加初始状态
        m.add_state("diagnose_trigger", Transition.diagnose_trigger_transitions)
        m.add_state("emerge_trigger", Transition.emerge_trigger_transitions)
        m.add_state("have_trigger", Transition.have_trigger_transitions)
        m.add_state("stop_trigger", Transition.stop_trigger_transitions)  # 添加最终状态
        m.add_state("end", None, end_state=1)
        m.add_state("error", None, end_state=1)
        m.set_start("Start")
        return m

    @staticmethod
    def start_transitions(ent_list, index=0):
        word = ent_list[index]

        if word == "诊断":
            newState = "diagnose_trigger"
        elif word == "出现":
            newState = "emerge_trigger"
        elif word == "有":
            newState = "have_trigger"
        else:
            newState = "end"
        return newState, index+1

    @staticmethod
    def diagnose_trigger_transitions(ent_list, index):
        word = ent_list[index]
        if word == "给予":
            newState = "end"
        elif word == "服":
            newState = "end"
        elif word == "予以":
            newState = "end"
        elif word == "服用":
            newState = "end"
        else:
            newState = "error"

        return newState, index+1

    @staticmethod
    def emerge_trigger_transitions(ent_list, index):
        word = ent_list[index]
        if word == "停用":
            newState = "stop_trigger"
        elif word == "予以":
            newState = "end"
        elif word == "给予":
            newState = "end"
        elif word == "服":
            newState = "end"
        elif word == "服用":
            newState = "end"
        else:
            newState = "error"
        return newState, index+1

    @staticmethod
    def stop_trigger_transitions(ent_list, index):
        word = ent_list[index]
        if word == "予以":
            newState = "end"
        elif word == "给予":
            newState = "end"
        else:
            newState = "error"
        return newState, index+1

    @staticmethod
    def have_trigger_transitions(ent_list, index):
        word = ent_list[index]
        if word == "应用":
            newState = "end"
        elif word == "给予":
            newState = "end"
        else:
            newState = "error"
        return newState, index + 1

act_label_dic = {
    "诊断": ["dis", "sym"],
    "给予": ["tot", "med"],
    "行": ["sur", "tot"],
    "服": ["med"],
    "服用": ["med"],
    "出现": ["dis", "sym"],
    "停用": ["tot", "med"],
    "予以": ["tot", "med"],
    "有": ["sym", "dis"],
    "应用": ["med", "tot"]
}
model = Transition._construct_model()

class FSM(object):
    @classmethod
    def build_relationship(cls, tree, ent_list, ent_relship):
        rel_tokens = cls.get_rel_tokens(model, tree)
        for token_trigger, token_recv in rel_tokens:
            trigger_word, recv_word = token_trigger.word, token_recv.word
            trigger_label, recv_label = act_label_dic.get(trigger_word), act_label_dic.get(recv_word)
            triggers, recvs = [], []
            for trigger_child in token_trigger.right_child:
                if trigger_child.tag in trigger_label:
                    triggers.append(ent_list.get(trigger_child.entity_id))
                    for ent_id in trigger_child.jutx_child:
                        triggers.append(ent_list.get(ent_id))
            for recv_child in token_recv.right_child:
                if recv_child.tag in recv_label:
                    recvs.append(ent_list.get(recv_child.entity_id))
                    for ent_id in recv_child.jutx_child:
                        recvs.append(ent_list.get(ent_id))
            if triggers and recvs:
                for trigger_ent_obj in triggers:
                    trigger_tag = trigger_ent_obj.get("label")
                    for recv_ent_obj in recvs:
                        recv_tag = recv_ent_obj.get("label")
                        relation_type = KernelNLPConfig.get_entity_relation_type(trigger_tag, recv_tag)
                        if relation_type:
                            ent_relship.add_entity_relationship(trigger_ent_obj, recv_ent_obj, relation_type)

    @classmethod
    def get_rel_tokens(cls, model, tree):
        rel_tokens = []
        act_tokens = cls.extract_act_tokens(tree)
        for act_pairs in act_tokens:
            act_words = [token.word for token in act_pairs]
            index, status = model.run(act_words)
            if status == "error":
                continue
            amend_token_pairs = act_pairs[0:index]
            token_trigger = amend_token_pairs[0]
            for token in amend_token_pairs[1:]:
                rel_tokens.append((token_trigger, token))
        return rel_tokens

    @classmethod
    def extract_act_tokens(cls, tree):
        """提取tree中连续的act对"""
        tokens = tree.root.right_child
        act_tokens = []
        index = 0
        length = len(tokens)
        if length < 2:
            return act_tokens
        while index < length:
            cur_token = tokens[index]
            cur_tag = cur_token.tag
            if not cur_tag == "act":
                index += 1
                continue
            next_idx = index + 1
            act_pairs = []
            act_pairs.append(cur_token)
            while next_idx < length:
                next_token = tokens[next_idx]
                next_tag = next_token.tag
                if next_tag == "act":
                    act_pairs.append(next_token)
                    next_idx += 1
                else:
                    break
            if len(act_pairs) >= 2:
                act_tokens.append(act_pairs)

            index = next_idx + 1

        return act_tokens


if __name__ == "__main__":
    pass
