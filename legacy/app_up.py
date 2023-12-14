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


# 리뷰 표시를 위한 페이지네이션 함수
def paginated_reviews(reviews, page_number, reviews_per_page=100):
    start = (page_number - 1) * reviews_per_page
    end = start + reviews_per_page
    return [html.P(review) for review in reviews[start:end]]

# 긍정 및 부정 리뷰 비율을 위한 게이지 차트 생성 함수
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
        figure=create_gauge_chart(positive_reviews, negative_reviews),
        config={'displayModeBar': False},
        style={'width': '50%', 'margin': 'auto'},
    ),

    # 리뷰 섹션
    html.Div([
        # 긍정 리뷰 토글 버튼 및 섹션
        html.Button("긍정 리뷰 보기/숨기기", id="toggle-positive"),
        html.Div(id="positive-reviews-section", style={"display": "none"}),

        # 부정 리뷰 토글 버튼 및 섹션
        html.Button("부정 리뷰 보기/숨기기", id="toggle-negative"),
        html.Div(id="negative-reviews-section", style={"display": "none"}),

        # 모든 리뷰 토글 버튼 및 섹션
        html.Button("모든 리뷰 보기/숨기기", id="toggle-all-reviews"),
        html.Div(id="all-reviews-section", style={"display": "none"}),
    ]),

    # 워드 클라우드 이미지
    html.Img(id='wordcloud-image', style={"display": "none"}),

    # 워드 클라우드 표시 버튼
    html.Div([
        html.Button("전체 리뷰 워드클라우드 보기", id="show-all-wc"),
        html.Button("긍정 리뷰 워드클라우드 보기", id="show-positive-wc"),
        html.Button("부정 리뷰 워드클라우드 보기", id="show-negative-wc"),
    ]),

    # 페이지네이션 컴포넌트
    html.Div([
        html.Button('이전', id='prev-button'),
        html.Button('다음', id='next-button'),
        html.Div(id='review-page-number', children='1', style={'display': 'none'}),
    ]),
    html.Div(id='review-section'),
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


# 콜백 함수들
@app.callback(
    Output('positive-reviews-section', 'children'),
    [Input('toggle-positive', 'n_clicks')],
    [State('review-page-number', 'children')]
)
def display_positive_reviews(n_clicks, page_number):
    if n_clicks and n_clicks % 2 != 0:
        return paginated_reviews(positive_reviews, int(page_number))
    return []

@app.callback(
    Output('negative-reviews-section', 'children'),
    [Input('toggle-negative', 'n_clicks')],
    [State('review-page-number', 'children')]
)
def display_negative_reviews(n_clicks, page_number):
    if n_clicks and n_clicks % 2 != 0:
        return paginated_reviews(negative_reviews, int(page_number))
    return []

@app.callback(
    Output('all-reviews-section', 'children'),
    [Input('toggle-all-reviews', 'n_clicks')],
    [State('review-page-number', 'children')]
)
def display_all_reviews(n_clicks, page_number):
    if n_clicks and n_clicks % 2 != 0:
        all_reviews = df['comment'].tolist()
        return paginated_reviews(all_reviews, int(page_number))
    return []

@app.callback(
    Output('wordcloud-image', 'src'),
    [Input('show-all-wc', 'n_clicks'), 
     Input('show-positive-wc', 'n_clicks'), 
     Input('show-negative-wc', 'n_clicks')],
    [State('wordcloud-image', 'src')]
)
def update_wordcloud_image(show_all_clicks, show_positive_clicks, show_negative_clicks, current_src):
    ctx = dash.callback_context
    if not ctx.triggered:
        # 기본값으로 전체 리뷰의 워드클라우드를 표시
        img_src = generate_wordcloud(df['comment'].tolist())
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'show-positive-wc':
            img_src = generate_wordcloud(positive_reviews)
        elif button_id == 'show-negative-wc':
            img_src = generate_wordcloud(negative_reviews)
        else:
            img_src = current_src  # 변경 없음
    return img_src

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
