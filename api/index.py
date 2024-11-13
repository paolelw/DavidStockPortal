from flask import Flask, request, jsonify, send_from_directory
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置Tushare API token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '68babfef29946cefbb30be591fef6e3c274637639d31644be740d81f')
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 从app.py复制INDUSTRY_THEMES
INDUSTRY_THEMES = {
    # ... (与app.py中的INDUSTRY_THEMES相同)
}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists("static/" + path):
        return send_from_directory('static', path)
    return send_from_directory('.', 'index.html')

@app.route('/api/query_stock', methods=['POST'])
def query_stock():
    try:
        stock_code = request.json.get('stock_code')
        logger.info(f"Querying stock: {stock_code}")
        
        if not stock_code:
            return jsonify({'success': False, 'error': '股票代码不能为空'})
        
        # 计算一年前的日期
        end_date = datetime.now()
        start_date = (end_date - timedelta(days=365)).strftime('%Y%m%d')
        end_date = end_date.strftime('%Y%m%d')
        
        # ... (与app.py中的query_stock函数其余部分相同)
        
    except Exception as e:
        logger.error(f"Error querying stock {stock_code}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'查询失败：{str(e)}'})

# 添加错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "服务器内部错误，请稍后重试"
    }), 500

# 其他路由和函数... 