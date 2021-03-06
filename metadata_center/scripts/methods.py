import sys
import argparse
from .run_cmd import run


def parser_args(params):
    """[summary]
    解析命令行参数.

    Args:
        params ([type]): 要解析的参数
        get_cmd_func ([type]): 根据命令名获取对应命令函数的工厂函数
    """

    parser = argparse.ArgumentParser(
        prog='metadata_center',
        description='管理http应用的命令行工具',
        epilog='子命令run可以用来启动服务'
    )
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(
        title='子解析',
        description='指定主机端口或配置文件启动http服务',
        help='支持的子解析'
    )
    # 启动服务所用的解析
    parser_run = subparsers.add_parser(
        "run",
        help='指定主机端口或配置文件启动http服务'
    )
    parser_run.add_argument("--port", type=int, help="指定端口")
    parser_run.add_argument("--host", type=str, help="指定主机")
    parser_run.add_argument("--nodebug", action="store_true", help="是否使用debug模式")
    parser_run.add_argument("-c", '--config', type=str, help="指定配置文件,使用json进行配置")
    parser_run.set_defaults(func=run)
    args = parser.parse_args(params)
    args.func(args)


def main(argv=sys.argv[1:]):
    """服务启动入口.

    设置覆盖顺序`环境变量>命令行参数`>`'-c'指定的配置文件`>`项目启动位置的配置文件`>默认配置.
    """
    parser_args(argv)
