import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
from wordcloud import WordCloud
import base64
from io import BytesIO
import plotly.graph_objs as go
import math

# 데이터 로드 및 전처리
df = pd.read_csv('data/ground_truth_and_predictions_electra.csv')
df = df.dropna(subset=['comment'])  # NaN 값을 제거
positive_reviews = df[df['sentiment_predicted'] == 1]['comment'].tolist()
negative_reviews = df[df['sentiment_predicted'] == 0]['comment'].tolist()

# 워드 클라우드 생성 함수
def generate_wordcloud(reviews):
    text = ' '.join(str(review) for review in reviews)  # 모든 리뷰를 문자열로 변환
    wordcloud = WordCloud(font_path='NanumGothic.ttf', background_color='white').generate(text)
    img_buffer = BytesIO()
    wordcloud.to_image().save(img_buffer, format="PNG")
    img_str = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
    return img_str

# 대시 애플리케이션 초기화
app = dash.Dash(__name__)

# 페이지당 리뷰 수 설정
REVIEWS_PER_PAGE = 100

# 페이지네이션을 위한 리뷰 분할 함수
def get_paginated_reviews(reviews, page_number):
    start = (page_number - 1) * REVIEWS_PER_PAGE
    end = start + REVIEWS_PER_PAGE
    return reviews[start:end]

# Create a custom gauge chart for sentiment distribution
def create_gauge_chart(positive_reviews, negative_reviews):
    total_reviews = len(positive_reviews) + len(negative_reviews)
    positive_percentage = len(positive_reviews) / total_reviews * 100

    gauge_chart = go.Figure(go.Indicator(
        mode="gauge+number",
        value=positive_percentage,
        title={'text': '긍정 vs 부정 리뷰'},
        gauge={'axis': {'visible': False},
               'bar': {'color': 'green'},
               'threshold': {
                   'line': {'color': 'red', 'width': 4},
                   'thickness': 0.75,
                   'value': 50
               }}
    ))

    gauge_chart.update_layout(
        title='긍정 vs 부정 리뷰 비율',
        template={'data': {'indicator': [{'title': '긍정'}]}}
    )

    return gauge_chart

# App layout
app.layout = html.Div([
    # Custom gauge chart for sentiment distribution
    dcc.Graph(
        id='sentiment-gauge',
        config={'displayModeBar': False},
        style={'width': '50%', 'margin': 'auto'},
    ),

    # 토글 버튼 및 리뷰 섹션
    html.Div([
        html.Button("Show/Hide Positive Reviews", id="toggle-positive"),
        html.Div(
            [html.P(review) for review in positive_reviews],
            id="positive-reviews-section",
            style={"display": "none"}
        ),

        html.Button("Show/Hide Negative Reviews", id="toggle-negative"),
        html.Div(
            [html.P(review) for review in negative_reviews],
            id="negative-reviews-section",
            style={"display": "none"}
        ),

        html.Button("Show/Hide All Reviews", id="toggle-all-reviews"),
        html.Div(
            id="all-reviews-section",
            style={"display": "none"}
        ),
    ]),

    # 워드 클라우드 이미지
    html.Img(id='wordcloud-image', style={"display": "block"}),

    # 워드 클라우드 표시 버튼
    html.Div([
        html.Button("Show WordCloud for All Reviews", id="show-all-wc"),
        html.Button("Show WordCloud for Positive Reviews", id="show-positive-wc"),
        html.Button("Show WordCloud for Negative Reviews", id="show-negative-wc"),
    ]),

    # 페이지네이션 컴포넌트
    html.Div([
        html.Button('Previous', id='prev-button'),
        html.Button('Next', id='next-button'),
        html.Div(id='review-page-number', children='1', style={'display': 'none'}),
    ]),
    html.Div(id='review-section'),
])

# 리뷰 섹션을 위한 페이지네이션 함수
def paginated_reviews(reviews, page_number):
    start = (page_number - 1) * REVIEWS_PER_PAGE
    end = start + REVIEWS_PER_PAGE
    return [html.P(review) for review in reviews[start:end]]

# Callback to update the gauge chart
@app.callback(
    Output('sentiment-gauge', 'figure'),
    [Input('toggle-positive', 'n_clicks')]
)
def update_gauge_chart(n_clicks):
    return create_gauge_chart(positive_reviews, negative_reviews)

# Callbacks for toggling review sections
@app.callback(
    Output('positive-reviews-section', 'style'),
    [Input('toggle-positive', 'n_clicks')]
)
def toggle_positive_section(n_clicks):
    if n_clicks and n_clicks % 2 != 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('negative-reviews-section', 'style'),
    [Input('toggle-negative', 'n_clicks')]
)
def toggle_negative_section(n_clicks):
    if n_clicks and n_clicks % 2 != 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('all-reviews-section', 'style'),
    [Input('toggle-all-reviews', 'n_clicks')]
)
def toggle_all_reviews_section(n_clicks):
    if n_clicks and n_clicks % 2 != 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# Callback for updating review section
@app.callback(
    Output('review-section', 'children'),
    [Input('review-page-number', 'children'),
     Input('toggle-positive', 'n_clicks'),
     Input('toggle-negative', 'n_clicks'),
     Input('toggle-all-reviews', 'n_clicks')]
)
def update_review_section(current_page, toggle_positive, toggle_negative, toggle_all_reviews):
    if toggle_positive and toggle_positive % 2 != 0:
        reviews = get_paginated_reviews(positive_reviews, int(current_page))
    elif toggle_negative and toggle_negative % 2 != 0:
        reviews = get_paginated_reviews(negative_reviews, int(current_page))
    elif toggle_all_reviews and toggle_all_reviews % 2 != 0:
        reviews = get_paginated_reviews(df['comment'].tolist(), int(current_page))
    else:
        reviews = []

    return reviews

# Callback for updating word cloud image
@app.callback(
    Output('wordcloud-image', 'src'),
    [Input('show-all-wc', 'n_clicks'), 
     Input('show-positive-wc', 'n_clicks'), 
     Input('show-negative-wc', 'n_clicks')]
)
def update_wordcloud_image(show_all_clicks, show_positive_clicks, show_negative_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        img_src = generate_wordcloud(df['comment'].tolist())
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'show-positive-wc':
            img_src = generate_wordcloud(positive_reviews)
        elif button_id == 'show-negative-wc':
            img_src = generate_wordcloud(negative_reviews)
        else:
            img_src = generate_wordcloud(df['comment'].tolist())
    
    return img_src

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
