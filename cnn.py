import numpy as np
import pandas as pd
import os

from PIL import Image
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import BatchNormalization

data_path = '/mnt/elice/dataset/' 

# 데이터 이름과 라벨이 있는 csv 파일을 읽어옵니다.
train_file_list = pd.read_csv(os.path.join(data_path, "train_files.csv"), index_col=0)
test_file_list = pd.read_csv(os.path.join(data_path, "test_files.csv"), index_col=0)

# 실제 데이터가 있는 경로를 지정해줍니다.
train_data_path = os.path.join(data_path, "train")
test_data_path = os.path.join(data_path, "test")

# 이미지 데이터를 불러와서 32x32로 resize하고, 리스트에 저장합니다.
train_img_all = []
train_label_all = []

test_img_all = []

for index, label in train_file_list.iterrows():
    img = Image.open(os.path.join(train_data_path, index))
    img_resized = img.resize((32, 32))
    img_resized = np.array(img_resized)
    train_img_all.append(img_resized)
    train_label_all.append(label["label"])

for index, label in test_file_list.iterrows():
    img = Image.open(os.path.join(test_data_path, index))
    img_resized = img.resize((32, 32))
    img_resized = np.array(img_resized)
    test_img_all.append(img_resized)

train_img_all = np.array(train_img_all)
train_label_all = np.array(train_label_all)
test_img_all = np.array(test_img_all)

# 라벨을 one-hot 인코딩
label_mapping = {'vehicle': 0, 'person': 1, 'others': 2}
train_label_all = np.array([label_mapping[label] for label in train_label_all])
train_label_all = to_categorical(train_label_all, num_classes=3)

# 데이터셋 만들기
x_train, x_val, y_train, y_val = train_test_split(
    train_img_all, train_label_all, test_size=0.1, random_state=42
)

# CNN 모델 생성
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
    BatchNormalization(),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D((2, 2)),
    Conv2D(128, (3, 3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(3, activation='softmax')
])

optimizer = Adam(learning_rate=0.001)  # 학습률 조정
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])
#model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 데이터 증강
datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    zoom_range=0.2,  # 확대/축소 범위 추가
)

datagen.fit(x_train)

# 모델 학습
#early_stopping = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)
history = model.fit(datagen.flow(x_train, y_train, batch_size=32), epochs=150, validation_data=(x_val, y_val))
#history = model.fit(datagen.flow(x_train, y_train, batch_size=32), epochs=60, validation_data=(x_val, y_val), callbacks=[early_stopping])


# 검증용 데이터셋에 대한 정확도 계산
val_loss, val_accuracy = model.evaluate(x_val, y_val)
print("Validation Accuracy:", val_accuracy)

# 테스트 데이터 예측
test_predictions = model.predict(test_img_all)
test_labels = np.argmax(test_predictions, axis=1)

# 라벨을 원래 문자열로 변환
reverse_label_mapping = {v: k for k, v in label_mapping.items()}
test_file_list["label"] = [reverse_label_mapping[label] for label in test_labels]
test_file_list.to_csv("submission.csv")

submission = pd.read_csv("submission.csv", index_col='file')
submission