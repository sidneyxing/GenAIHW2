# How to run the website

1. open terminal
2. type
```
cd frontend
```
3. type
```
python -m http.server 5500
```
4. open
```
http://localhost:5500
```

# Backend
```
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

# Swith to API mode
1. inside api.js, change this USE_API: false, to this USE_API: true
2. inside index.html, delete line 73