# -*- coding: utf-8 -*-
__all__ = ['sample_data']

from datetime import datetime


_now = datetime.now()

sample_data = {
    'now': _now,

    'parents': [
        dict(cstr='par1'),
        dict(cstr='par2')
    ],

    # 合法数据
    'normal_entities': [
        # 所有数值都填上
        dict(parent_id=1, cint_n=11, cstr=u'一二三四', cstr_n='abcdefg', cfl=1.23, cfl_n=2.35,
             cbl=False, cbl_n=True, cts=_now, cts_n=_now),
        # 只填上必填（nullable=False且没有默认值的）数值
        dict(parent_id=2, cstr='xyz', cts=_now),
        # 填上一部分选填数值
        dict(parent_id=2, cint_n=15, cstr=u'一', cfl=1.23, cfl_n=2.35, cts=_now),
        dict(parent_id=1, cstr=u'一', cstr_n=u'xxc', cbl=False, cts=_now),
    ],

    # 非法数据
    # 测试各验证器是否有效，以及是否能够跳过 None 值
    'invalid_entities': [
        # cint_n min
        dict(parent_id=1, cint_n=9, cstr=u'一二三四', cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cint_n=3, cstr=u'一二三四', cfl=1.23, cbl=False, cts=_now),
        # cint_n max
        dict(parent_id=1, cint_n=21, cstr=u'一二三四', cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cint_n=25, cstr=u'一二三四', cfl=1.23, cbl=False, cts=_now),
        # cstr min_length
        dict(parent_id=1, cstr=u'', cfl=1.23, cbl=False, cts=_now),
        # cstr max_length
        dict(parent_id=1, cstr=u'一二三四五', cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cstr=u'12345', cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cstr='abcde', cfl=1.23, cbl=False, cts=_now),
        # cstr_n match
        dict(parent_id=1, cstr=u'一二三', cstr_n='abCde', cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cstr=u'一二三', cstr_n=u'ab-de', cfl=1.23, cbl=False, cts=_now),
        # cint_n custom
        dict(parent_id=1, cstr=u'一二三', cint_n=2, cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cstr=u'一二三', cint_n=20, cfl=1.23, cbl=False, cts=_now),
        dict(parent_id=1, cstr=u'一二三', cint_n=16, cfl=1.23, cbl=False, cts=_now),
    ]
}