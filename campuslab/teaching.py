"""Educates teaching action adaptation, changed for CampusLab on 2026-11-09.

Copyright 2020-2026 The Educates Authors. Apache-2.0; see
docs/third-party/educates/LICENSE and NOTICE. Adapted from
examiner-execute-test.html and clickable-action.html at d7e018f0cee382a595d2c9ecc6c938da099eb67e.
Hugo/HTTP examiner dispatch is replaced by fixed report checks and manual recollection.
No upstream shell arguments, autostart, unlimited retries or inline script are accepted.
"""
import re

CHECK_TITLES = {
    'os': '操作系统', 'python': '课程Python', 'node': '课程Node', 'npm': '关联npm', 'run': '固定程序',
    'package:requests': 'requests', 'package:torch': 'PyTorch', 'package:transformers': 'Transformers',
    'model:weights': '固定模型权重', 'model:inference': '固定本地推理',
    'torch:import': 'PyTorch实际导入', 'torch:cpu': 'CPU张量', 'torch:cuda-build': 'CUDA构建',
    'torch:gpu-available': 'GPU可用性', 'torch:gpu-identity': 'GPU身份', 'torch:gpu-run': 'GPU实算',
    'host:virtualization': '宿主虚拟化', 'vm:software': '虚拟化软件', 'vm:instance': '虚拟机实例',
    'vm:running': '实例运行', 'guest:identity': '来宾身份', 'guest:linux': 'Linux来宾', 'guest:run': '来宾固定运行',
    'dsh:software': 'DSH安装身份', 'dsh:node': 'DSH所选Node', 'dsh:workspace': '专用练习目录',
    'dsh:model': '实际模型接入', 'dsh:permission': '本人实际授权', 'dsh:tools': '实际工具回合', 'dsh:artifact': '固定产物',
    'notebook:kernel': 'Notebook内核', 'notebook:identity': '内核解释器关联', 'notebook:run': '固定数据计算',
    'package:jupyter_client': 'Jupyter客户端', 'package:ipykernel': 'Python内核组件',
    'notebook:spec': '所选内核定义', 'notebook:cleanup': '本次临时内核清理',
    'package:numpy': 'NumPy', 'package:pandas': 'Pandas', 'java:identity': 'JDK同源身份',
    'java:version': 'Java版本', 'javac:version': 'javac版本', 'java:run': '固定编译运行',
    'java:java': '所选Java运行时', 'java:javac': '同JDK编译器', 'java:compile': '固定源码编译',
    'sqlite:identity': 'SQLite文件身份', 'sqlite:version': 'SQLite版本', 'sqlite:query': '固定只读查询',
    'sqlite:runtime': 'SQLite运行时', 'sqlite:database': '显式数据库文件', 'sqlite:readonly': '只读连接',
    'api:destination': 'API目的地', 'api:configuration': '本人配置', 'api:protocol': 'API协议', 'api:result': '固定课程响应',
    'api:dependency': 'API编程环境', 'api:request': 'API实际请求', 'api:exercise': '固定API练习',
    'web:record': '本人网页练习记录', 'web:artifact': '网页课程成果', 'web:connection': '自动登录检测',
    'web:workspace': '网页练习目录', 'web:self-record': '本人网页练习记录', 'web:login': '自动登录检测',
}


def validate_action(action):
    if not isinstance(action, dict) or set(action) != {'name', 'title', 'description', 'cooldown'}:
        raise ValueError('教学步骤只支持固定名称、标题、说明和冷却时间')
    if action['name'] not in CHECK_TITLES or action['cooldown'] != 3 or type(action['cooldown']) is not int:
        raise ValueError('教学步骤必须绑定已审查固定检查')
    if any(not isinstance(action[k], str) or not 1 <= len(action[k]) <= 1000 for k in ('title', 'description')):
        raise ValueError('教学步骤说明无效')
    return action


def lesson_checks(result):
    if not isinstance(result, dict) or not re.fullmatch('[a-f0-9]{64}', result.get('task_id', '')) or not isinstance(result.get('checks'), list):
        raise ValueError('教学检查需要当前已分析的固定任务报告')
    items = []
    for check in result['checks']:
        if not isinstance(check, dict) or check.get('id') not in CHECK_TITLES or check.get('status') not in ('pass', 'missing', 'mismatch', 'unknown'):
            raise ValueError('教学检查不能分派任意命令或未知检查')
        status = check['status']
        description = {'pass': '已有报告符合本项固定要求。保持原件，再手动采集较晚的同目标报告。',
                       'missing': '当前所选目标缺少所需组件。按具体指导由本人准备，再采集同目标新报告。',
                       'mismatch': '观察值与要求不符。展开原始证据核对差异，手动处理后复检。',
                       'unknown': '证据不足。先补齐本项实际观察；阅读或勾选不会让它通过。'}[status]
        action = validate_action(dict(name=check['id'], title=CHECK_TITLES[check['id']], description=description, cooldown=3))
        items.append(dict(**action, task_id=result['task_id'], status=status, success=status == 'pass',
                          action='manual-recollect', source='Educates教学动作模板适配；结果来自课航确定性报告'))
    return items
