# 1. Use a Python-based image
FROM python:3.10-alpine
# 2. Create a working directory and change there
ADD app.py .

# 3. Copy the dependency file (requirements.txt is copied first so that the cache is used if it doesn't change)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-dependencies --no-cache-dir -r requirements.txt

# 5. Copy the Python files
COPY . .

# 6. Command to run
CMD ["python", "app.py","--host=0.0.0.0"]