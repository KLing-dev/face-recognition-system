from app.api import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 从配置文件导入HOST和PORT
    try:
        from app.config import HOST, PORT
        app.run(host=HOST, port=PORT, debug=True)
    except ImportError:
        # 如果配置文件不存在，使用默认值
        app.run(host='127.0.0.1', port=5000, debug=True)