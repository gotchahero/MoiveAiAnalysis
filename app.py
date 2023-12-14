from flask import Flask, render_template, url_for
import csv
import chardet
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import urllib.parse

app = Flask(__name__)


# URL 인코딩 필터 정의
def url_encode_filter(s):
    return urllib.parse.quote_plus(s)

# 필터를 Flask 앱에 추가
app.jinja_env.filters['url_encode'] = url_encode_filter

# 영화 이미지 파일이 있는 로컬 폴더 경로
movie_image_folder = 'static/images/movies'

# 영화 이미지 파일 목록을 읽어옴
movie_image_files = os.listdir(movie_image_folder)
movie_image_files = [filename for filename in movie_image_files if filename.endswith('.jpg')]

# URL에 적합하게 영화 제목 변환
def format_movie_title(title):
    return title.replace(' ', '_').lower()

# 영화 정보 데이터 초기화
movies = []

# 이미지 파일 목록을 기반으로 영화 정보 추가
for i, image_file in enumerate(movie_image_files):
    title = os.path.splitext(image_file.split('_', 1)[1])[0]
    image_url = os.path.join(movie_image_folder, image_file).replace('\\', '/')
    movie_url = format_movie_title(title)
    left = 323 + (i % 5) * 260
    top = 530 + (i // 5) * 440
    movies.append({"title": title, "image_url": image_url, "left": left, "top": top, "url": movie_url})

@app.route('/')
def movie_info():
    return render_template('movie_info.html', movies=movies)

# 이미지 파일이 있는 로컬 폴더 경로
image_folder = 'static/images/movies/actors'

# 로컬 폴더에서 이미지 파일 목록을 읽어옴
image_files = os.listdir(image_folder)

# 이미지 파일 목록에서 확장자가 .jpg 인 파일만 필터링
image_files = [filename for filename in image_files if filename.endswith('.jpg')]

# 출연진 정보 데이터를 초기화
cast_info = []

# 이미지 파일 목록을 기반으로 출연진 정보 추가
for image_file in image_files:
    # 파일명에서 숫자와 밑줄 제거하여 이름 추출 (예: "1_마동석.jpg" -> "마동석")
    actor_name = os.path.splitext(image_file.split('_', 1)[1])[0]

    # 출연진 정보 생성 및 추가
    # 이미지 파일의 로컬 경로를 지정 (슬래시를 사용하여 경로 수정)
    actor_info = {"name": actor_name, "image_url": os.path.join(image_folder, image_file).replace('\\', '/')}
    cast_info.append(actor_info)

def detect_csv_encoding(file_path):
    with open(file_path, 'rb') as csvfile:
        result = chardet.detect(csvfile.read())
        return result['encoding']

@app.route('/범죄도시2')
def movie():
    positive_reviews = []
    negative_reviews = []

    # CSV 파일 인코딩 감지
    csv_file_path = 'data/ground_truth_and_predictions_electra.csv'
    encoding = detect_csv_encoding(csv_file_path)

    # CSV 파일 열기
    with open(csv_file_path, 'r', encoding=encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            review_text = row['comment']
            sentiment = row['sentiment_predicted']

            # 리뷰가 비어 있지 않은 경우에만 추가
            if review_text.strip() != "":
                sentiment = int(sentiment)
                if sentiment == 1:
                    positive_reviews.append(review_text)
                else:
                    negative_reviews.append(review_text) 

    # Flask 앱에서 이 이미지를 HTML에 표시하는 코드 추가
    # 긍정 및 부정 리뷰의 수와 비율 계산
                    
    total_reviews = len(positive_reviews) + len(negative_reviews)
    if total_reviews > 0:
        positive_percentage = round((len(positive_reviews) / total_reviews) * 100, 1)
        negative_percentage = round((len(negative_reviews) / total_reviews) * 100, 1)
    else:
        positive_percentage = 0.0
        negative_percentage = 0.0

    return render_template('movie.html', positive_reviews=positive_reviews, negative_reviews=negative_reviews, positive_percentage=positive_percentage, negative_percentage=negative_percentage, cast_info=cast_info)

if __name__ == '__main__':
    app.run(debug=True)
