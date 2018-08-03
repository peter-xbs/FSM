# -*- coding:utf-8 -*-
import os
from parse_tree.utils.utils import TreeProducer
from parse_tree.parse.tree_process import TreeProcess
from process.entity_relationship import EntityRelationship
from parse_tree.utils.visualization_tools import TreeView
from kernel_nlp.kernel_nlp_config import KernelNLPConfig
from parse_tree.utils.output2excel import Output2Excl
from parse_tree.utils.output_entity_test import Output2Excl as out_test


class ParserProcess(object):
    """
    数据入口处理引擎，树的生成及无环检验
    """
    def __init__(self, entity_relationship):
        self.entity_relationship = entity_relationship

    def process(self, input_file):
        # 实体列表汇总
        total_entity_list = list()

        # 生成树列表
        if input_file.endswith('.xls'):
            sentences, tree_list, sentences_value_list = TreeProducer.read_excel(input_file)
        else:
            sentences, tree_list, sentences_value_list = TreeProducer.read_text(input_file)

        # 依次对每一棵树进行处理，并返回实体列表
        for tree in tree_list:
            tree_ent_list = TreeProcess(self.entity_relationship, tree).process()
            total_entity_list.append(tree_ent_list)

        return total_entity_list, sentences_value_list, tree_list, sentences


def visualize():
    def tree_select1(tree):
        """选取root下直连act数目>=2的树"""
        flag = False
        act_num = 0
        root_token = tree.root
        root_child_tokens = root_token.left_child + root_token.right_child
        for token in root_child_tokens:
            if token.tag == 'act':
                act_num += 1
            if act_num > 1:
                flag = True
                break
        return flag


    file = 'NLP实体关系badcase依存输出结果(含标点).conll'
    input_file = os.path.join(os.path.join('parse_tree/data', 'input'), file)
    output_file = os.path.join(os.path.join('parse_tree/data', 'output'), file)
    sentences, tree_list, sentences_value_list = TreeProducer.read_text(input_file)
    tree_sent_zip = zip(tree_list, sentences_value_list)
    for tree, sent_value in tree_sent_zip:
        # if tree_select2(tree):
        sent_val = ''.join(sent_value)
        TreeView.view_in_graph(tree, sent_val)
    TreeProducer.save_sentences(output_file+'.xls', sentences)


def main():
    # 加载NLP核心配置
    KernelNLPConfig.load_kernel_config()


    file = 'NLP属性badcase依存输出结果(1).conll'
    input_file = os.path.join(os.path.join('parse_tree/data', 'input'), file)
    output_file_visualize = os.path.join('parse_tree/data/output', 'visualize')
    format_output_file = os.path.join(os.path.join('parse_tree/data', 'output'), file)
    # 依存树的解析过程
    entity_relationship = EntityRelationship()
    parser_inst = ParserProcess(entity_relationship)
    total_entity_list, sentences_value_list, tree_list, sentences = parser_inst.process(input_file)

    # 输出保存格式化后的文件
    TreeProducer.save_sentences(format_output_file + '.xls', sentences)

    # 解析结果输出至excel中展示
    Output2Excl.process(output_file_visualize, total_entity_list, sentences_value_list, entity_relationship)

    # 树可视化
    tree_sent_zip = zip(tree_list, sentences_value_list)
    for tree, sent_value in tree_sent_zip:
        sent_value_len = len(sent_value)
        for i in range(sent_value_len):
            if i != 0 and i % 30 == 0:
                sent_value.insert(i, '\n')
        sent_val = ''.join(sent_value)
        TreeView.view_in_graph(tree, sent_val)

if __name__ == '__main__':
    visualize()
    main()
