from flask import Flask, render_template, jsonify, request
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在app初始化后添加错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "服务器内部错误，请稍后重试"
    }), 500

# 从环境变量获取Tushare API token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '68babfef29946cefbb30be591fef6e3c274637639d31644be740d81f')
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 行业主题映射
INDUSTRY_THEMES = {
    '银行': {
        'bg_color': 'bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900',
        'accent_color': 'blue',
        'icon': 'bank.svg',
        'chart_colors': ['#3B82F6', '#60A5FA', '#93C5FD'],
        'pattern': 'banking-pattern'
    },
    '证券': {
        'bg_color': 'bg-gradient-to-br from-purple-900 via-purple-800 to-fuchsia-900',
        'accent_color': 'purple',
        'icon': 'securities.svg',
        'chart_colors': ['#9333EA', '#A855F7', '#C084FC'],
        'pattern': 'securities-pattern'
    },
    '房地产': {
        'bg_color': 'bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-900',
        'accent_color': 'emerald',
        'icon': 'real-estate.svg',
        'chart_colors': ['#059669', '#10B981', '#34D399'],
        'pattern': 'realestate-pattern'
    },
    '医药生物': {
        'bg_color': 'bg-gradient-to-br from-rose-900 via-red-800 to-pink-900',
        'accent_color': 'rose',
        'icon': 'medical.svg',
        'chart_colors': ['#E11D48', '#F43F5E', '#FB7185'],
        'pattern': 'medical-pattern'
    },
    '计算机': {
        'bg_color': 'bg-gradient-to-br from-sky-900 via-cyan-800 to-blue-900',
        'accent_color': 'sky',
        'icon': 'tech.svg',
        'chart_colors': ['#0EA5E9', '#38BDF8', '#7DD3FC'],
        'pattern': 'tech-pattern'
    },
    '新能源': {
        'bg_color': 'bg-gradient-to-br from-lime-900 via-green-800 to-emerald-900',
        'accent_color': 'lime',
        'icon': 'energy.svg',
        'chart_colors': ['#84CC16', '#A3E635', '#BEF264'],
        'pattern': 'energy-pattern'
    },
    '消费': {
        'bg_color': 'bg-gradient-to-br from-amber-900 via-yellow-800 to-orange-900',
        'accent_color': 'amber',
        'icon': 'consumer.svg',
        'chart_colors': ['#F59E0B', '#FBBF24', '#FCD34D'],
        'pattern': 'consumer-pattern'
    },
    '电子': {
        'bg_color': 'bg-gradient-to-br from-indigo-900 via-violet-800 to-purple-900',
        'accent_color': 'indigo',
        'icon': 'tech.svg',
        'chart_colors': ['#6366F1', '#818CF8', '#A5B4FC'],
        'pattern': 'electronics-pattern'
    },
    '汽车': {
        'bg_color': 'bg-gradient-to-br from-zinc-900 via-slate-800 to-gray-900',
        'accent_color': 'zinc',
        'icon': 'consumer.svg',
        'chart_colors': ['#71717A', '#A1A1AA', '#D4D4D8'],
        'pattern': 'auto-pattern'
    },
    # 默认主题
    'default': {
        'bg_color': 'bg-gradient-to-br from-slate-900 via-gray-800 to-zinc-900',
        'accent_color': 'slate',
        'icon': 'default.svg',
        'chart_colors': ['#64748B', '#94A3B8', '#CBD5E1'],
        'pattern': 'default-pattern'
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query_stock', methods=['POST'])
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
        
        # 获取股票基本信息
        stock_info = pro.stock_basic(ts_code=stock_code, 
                                   fields='name,industry,market,list_date,fullname')
        
        if stock_info.empty:
            return jsonify({'success': False, 'error': '未找到该股票信息'})
        
        # 获取公司基本信息
        company_info = pro.stock_company(ts_code=stock_code, 
                                       fields='introduction,main_business,business_scope,chairman')
        
        # 获取股价数据
        stock_price = pro.daily(ts_code=stock_code, 
                              start_date=start_date,
                              end_date=end_date,
                              fields='trade_date,open,high,low,close,vol')
        
        if stock_price.empty:
            return jsonify({'success': False, 'error': '未找到股价数据'})
        
        # 获取行业主题
        industry = stock_info['industry'].iloc[0]
        theme = INDUSTRY_THEMES.get(industry, INDUSTRY_THEMES['default'])
        
        # 合并股票信息
        stock_name = stock_info['name'].iloc[0]
        stock_details = {
            'name': stock_name,
            'industry': industry or '未知行业',
            'market': stock_info['market'].iloc[0],
            'list_date': stock_info['list_date'].iloc[0] if 'list_date' in stock_info else '未知',
            'fullname': stock_info['fullname'].iloc[0] if 'fullname' in stock_info else stock_name,
            'chairman': company_info['chairman'].iloc[0] if not company_info.empty else '未知',
            'introduction': company_info['introduction'].iloc[0] if not company_info.empty else '暂无简介',
            'main_business': company_info['main_business'].iloc[0] if not company_info.empty else '暂无信息',
            'business_scope': company_info['business_scope'].iloc[0] if not company_info.empty else '暂无信息',
            'theme': theme
        }
        
        # 获取基本面数据
        basic_info = pro.daily_basic(ts_code=stock_code,
                                   start_date=start_date,
                                   end_date=end_date,
                                   fields='ts_code,trade_date,pe,pb,dv_ratio,total_mv')
        
        # 确保数据按日期排序并处理空值
        basic_info = basic_info.sort_values('trade_date')
        stock_price = stock_price.sort_values('trade_date')
        
        # 处理数据为图表格式
        data = {
            'stock_info': stock_details,
            'dates': basic_info['trade_date'].tolist(),
            'pe': basic_info['pe'].fillna(0).tolist(),
            'pb': basic_info['pb'].fillna(0).tolist(),
            'dv_ratio': basic_info['dv_ratio'].fillna(0).tolist(),
            'total_mv': (basic_info['total_mv'].fillna(0)/10000).tolist(),
            'price_data': {
                'dates': stock_price['trade_date'].tolist(),
                'open': stock_price['open'].tolist(),
                'high': stock_price['high'].tolist(),
                'low': stock_price['low'].tolist(),
                'close': stock_price['close'].tolist(),
                'vol': stock_price['vol'].tolist()
            }
        }
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error querying stock {stock_code}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'查询失败：{str(e)}'})

if __name__ == '__main__':
    # 本地运行使用debug模式
    app.run(debug=True)
else:
    # Vercel部署时使用
    app = app

# 只导入需要的模块
pd.options.mode.chained_assignment = None  # 关闭警告