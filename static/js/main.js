// 定义一个全局变量来存储所有图表实例
let charts = [];

function initChart(containerId, title) {
    const chart = echarts.init(document.getElementById(containerId));
    const option = {
        title: {
            text: title,
            textStyle: {
                color: '#fff'
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            axisLabel: {
                color: '#fff'
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                color: '#fff'
            }
        },
        series: [{
            type: 'line',
            smooth: true,
            lineStyle: {
                width: 3
            },
            itemStyle: {
                color: '#3b82f6'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(59,130,246,0.5)'
                }, {
                    offset: 1,
                    color: 'rgba(59,130,246,0.1)'
                }])
            }
        }]
    };
    chart.setOption(option);
    return chart;
}

// 添加错误提示函数
function showNotification(message, type = 'error') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-500 transform translate-x-full ${
        type === 'error' ? 'bg-red-600' : 'bg-green-600'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="text-white">${message}</span>
        </div>
    `;
    document.body.appendChild(notification);

    // 显示通知
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);

    // 自动关闭
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}

// 添加股票代码验证函数
function validateStockCode(code) {
    const pattern = /^[0-9]{6}\.(SH|SZ)$/;
    if (!pattern.test(code)) {
        showNotification('请输入正确的股票代码格式，例如：000001.SZ 或 600000.SH');
        return false;
    }
    return true;
}

// 修改查询函数，添加错误处理
async function queryStock() {
    const stockCode = document.getElementById('stockCode').value.trim().toUpperCase();
    if (!stockCode) {
        showNotification('请输入股票代码');
        return;
    }

    if (!validateStockCode(stockCode)) {
        return;
    }

    // 显示加载状态
    const button = document.querySelector('button');
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner"></span> 加载中...';

    try {
        const response = await fetch('/query_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ stock_code: stockCode })
        });

        const result = await response.json();
        if (result.success) {
            updateCharts(result.data);
            showNotification('数据加载成功', 'success');
        } else {
            showNotification(result.error);
        }
    } catch (error) {
        showNotification('网络错误，请稍后重试');
        console.error('Error:', error);
    } finally {
        // 恢复按钮状态
        button.disabled = false;
        button.textContent = originalText;
    }
}

// 添加图表错误处理
function updateCharts(data) {
    try {
        // 清空之前的图表实例
        charts.forEach(chart => {
            if (chart) {
                chart.dispose();
            }
        });
        charts = [];

        // 更新主题
        updateTheme(data.stock_info.theme);
        
        // 显示股票名称
        const stockInfo = document.getElementById('stockInfo');
        stockInfo.textContent = `${data.stock_info.name} (${document.getElementById('stockCode').value})`;
        stockInfo.classList.remove('hidden');

        // 显示公司信息
        const companyInfo = document.getElementById('companyInfo');
        companyInfo.classList.remove('hidden');

        // 更新公司详细信息
        updateCompanyInfo(data.stock_info);

        // 初始化并更新所有图表
        initializeCharts(data);

        // 添加窗口大小改变时的自适应
        window.addEventListener('resize', debounce(() => {
            charts.forEach(chart => {
                if (chart) {
                    chart.resize();
                }
            });
        }, 250));

    } catch (error) {
        showNotification('图表更新失败，请刷新页面重试');
        console.error('Chart update error:', error);
    }
}

// 添加防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 添加键盘事件监听
document.getElementById('stockCode').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        queryStock();
    }
});

// 添加页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    // 从URL参数中获取股票代码
    const urlParams = new URLSearchParams(window.location.search);
    const stockCode = urlParams.get('code');
    if (stockCode) {
        document.getElementById('stockCode').value = stockCode;
        queryStock();
    }
});

// 添加主题切换函数
function updateTheme(theme) {
    const background = document.getElementById('theme-background');
    const overlay = document.getElementById('background-overlay');
    const cards = document.querySelectorAll('.theme-card');
    const accentElements = document.querySelectorAll('.theme-accent');
    const buttons = document.querySelectorAll('.theme-button');
    
    // 更新背景
    background.className = `fixed inset-0 w-full h-full transition-all duration-500 ${theme.bg_color}`;
    
    // 更新背景图案
    overlay.className = `fixed inset-0 opacity-10 transition-all duration-500 ${theme.pattern}`;
    
    // 更新卡片样式
    cards.forEach(card => {
        // 更新卡片边框颜色
        card.style.borderColor = `var(--${theme.accent_color}-500)`;
        // 添加主题特定的阴影
        card.style.boxShadow = `0 4px 20px rgba(var(--${theme.accent_color}-500-rgb), 0.1)`;
    });
    
    // 更新按钮颜色
    buttons.forEach(button => {
        button.className = `w-full mt-4 bg-${theme.accent_color}-600 hover:bg-${theme.accent_color}-700 text-white font-bold py-2 px-4 rounded theme-button transition-all duration-300`;
    });
    
    // 更新强调色文本
    accentElements.forEach(el => {
        el.className = `text-lg font-bold text-${theme.accent_color}-400 theme-accent`;
    });
    
    // 更新图表颜色
    if (charts.length > 0) {
        charts.forEach(chart => {
            if (chart) {
                const option = chart.getOption();
                
                // 更新图表配色
                option.color = theme.chart_colors;
                
                // 更新K线图颜色（如果存在）
                if (option.series && option.series.find(s => s.type === 'candlestick')) {
                    const candlestickSeries = option.series.find(s => s.type === 'candlestick');
                    candlestickSeries.itemStyle = {
                        color: theme.chart_colors[0],
                        color0: theme.chart_colors[1],
                        borderColor: theme.chart_colors[0],
                        borderColor0: theme.chart_colors[1]
                    };
                }
                
                // 更新文字颜色
                if (option.title) {
                    option.title.textStyle = { color: '#fff' };
                }
                if (option.xAxis) {
                    if (Array.isArray(option.xAxis)) {
                        option.xAxis.forEach(axis => {
                            axis.axisLabel = { color: '#fff' };
                        });
                    } else {
                        option.xAxis.axisLabel = { color: '#fff' };
                    }
                }
                if (option.yAxis) {
                    if (Array.isArray(option.yAxis)) {
                        option.yAxis.forEach(axis => {
                            axis.axisLabel = { 
                                ...axis.axisLabel,
                                color: '#fff'
                            };
                        });
                    } else {
                        option.yAxis.axisLabel = { color: '#fff' };
                    }
                }
                if (option.legend) {
                    option.legend.textStyle = { color: '#fff' };
                }
                
                chart.setOption(option);
            }
        });
    }
} 