# 1. Python tabanlı imaj kullan
FROM python:3.10-alpine
# 2. Çalışma dizini oluştur ve oraya geç
ADD app.py .

# 3. Bağımlılık dosyasını kopyala (önce requirements.txt kopyalanır ki değişmezse cache kullanılsın)
COPY requirements.txt .

# 4. Bağımlılıkları yükle
RUN pip install --no-dependencies --no-cache-dir -r requirements.txt

   
# 5. Python dosyalarını kopyala
COPY . .

# 6. Çalıştırılacak komut
CMD ["python", "app.py","--host=0.0.0.0"]
