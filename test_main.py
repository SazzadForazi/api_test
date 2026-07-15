import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)

def get_auth_headers(username, password):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# 1. Main Route Tests
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Mock Sandbox API" in response.text

# 2. Auth Flow Tests
def test_auth_login_success():
    response = client.post("/api/v1/auth/login", json={"username": "tester", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "tester"
    assert "access_token" in response.cookies

def test_auth_login_failure():
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "detail" in response.json()

def test_auth_me_unauthorized():
    client.cookies.clear()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_auth_me_authorized_header():
    headers = get_auth_headers("admin", "password123")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"

def test_auth_me_authorized_cookie():
    # Login sets the cookie
    login_resp = client.post("/api/v1/auth/login", json={"username": "user", "password": "userpass"})
    assert login_resp.status_code == 200
    # Clear headers and rely on cookies
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "user"

def test_auth_logout():
    # Login to set cookie
    client.post("/api/v1/auth/login", json={"username": "user", "password": "userpass"})
    # Logout to clear
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
    # Check if cleared
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401

# 3. CRUD Tests
def test_crud_list_products():
    client.post("/api/v1/products/reset") # Make sure state is clean
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert data[0]["name"] == "Wireless Mouse"

def test_crud_list_with_query_params():
    client.post("/api/v1/products/reset")
    # Category filter
    response = client.get("/api/v1/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Price filters
    response = client.get("/api/v1/products?min_price=50")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Keyboard (79.99), Shoes (59.90)

def test_crud_get_single_product():
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    
    response = client.get("/api/v1/products/999")
    assert response.status_code == 404

def test_crud_create_rbac():
    client.post("/api/v1/products/reset")
    new_product = {
        "name": "Practice Book",
        "price": 15.00,
        "category": "Books",
        "in_stock": True,
        "description": "A notebook for API testing notes."
    }
    
    # 1. No auth
    response = client.post("/api/v1/products", json=new_product)
    assert response.status_code == 401
    
    # 2. 'user' role (Forbidden)
    user_headers = get_auth_headers("user", "userpass")
    response = client.post("/api/v1/products", json=new_product, headers=user_headers)
    assert response.status_code == 403
    
    # 3. 'tester' role (Created)
    tester_headers = get_auth_headers("tester", "testpass")
    response = client.post("/api/v1/products", json=new_product, headers=tester_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Practice Book"
    assert response.json()["id"] == 5

def test_crud_create_validation():
    tester_headers = get_auth_headers("tester", "testpass")
    # Invalid Price
    invalid_product = {
        "name": "Practice Book",
        "price": -5.0,
        "category": "Books",
        "in_stock": True
    }
    response = client.post("/api/v1/products", json=invalid_product, headers=tester_headers)
    assert response.status_code == 422
    
    # Invalid Category
    invalid_product2 = {
        "name": "Practice Book",
        "price": 10.0,
        "category": "Toys", # Not in allowed list
        "in_stock": True
    }
    response = client.post("/api/v1/products", json=invalid_product2, headers=tester_headers)
    assert response.status_code == 422

def test_crud_update():
    client.post("/api/v1/products/reset")
    tester_headers = get_auth_headers("tester", "testpass")
    update_data = {"price": 19.99, "in_stock": False}
    
    response = client.put("/api/v1/products/1", json=update_data, headers=tester_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 19.99
    assert data["in_stock"] is False
    # Unchanged fields remain
    assert data["name"] == "Wireless Mouse"

def test_crud_delete_rbac():
    client.post("/api/v1/products/reset")
    
    # 1. Tester try delete (Forbidden)
    tester_headers = get_auth_headers("tester", "testpass")
    response = client.delete("/api/v1/products/1", headers=tester_headers)
    assert response.status_code == 403
    
    # 2. Admin try delete (Success)
    admin_headers = get_auth_headers("admin", "password123")
    response = client.delete("/api/v1/products/1", headers=admin_headers)
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
    
    # Verify indeed deleted
    get_resp = client.get("/api/v1/products/1")
    assert get_resp.status_code == 404

# 4. Codec Tests
def test_base64_encode_decode():
    # Encode
    response = client.post("/api/v1/codec/base64/encode", json={"text": "Software Testing"})
    assert response.status_code == 200
    encoded = response.json()["encoded"]
    
    # Decode
    response_decode = client.post("/api/v1/codec/base64/decode", json={"code": encoded})
    assert response_decode.status_code == 200
    assert response_decode.json()["decoded"] == "Software Testing"

def test_base64_decode_invalid():
    response = client.post("/api/v1/codec/base64/decode", json={"code": "!!!NotBase64!!!"})
    assert response.status_code == 400

def test_jwt_decode_util():
    # Get a real token first
    login_resp = client.post("/api/v1/auth/login", json={"username": "tester", "password": "testpass"})
    token = login_resp.json()["access_token"]
    
    # Decode
    response = client.post("/api/v1/codec/jwt/decode", json={"token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["payload"]["sub"] == "tester"
    assert data["signature_verified_with_app_key"] is True

# 5. Simulators Tests
def test_delay_simulator():
    response = client.get("/api/v1/simulate/delay/1")
    assert response.status_code == 200
    assert response.json()["slept_seconds"] == 1

def test_status_simulator():
    for status_code in [200, 418, 500]:
        response = client.get(f"/api/v1/simulate/status/{status_code}")
        assert response.status_code == status_code
        if status_code != 204:
            assert response.json()["status_code"] == status_code

def test_headers_echo():
    response = client.get("/api/v1/simulate/headers", headers={"X-Test-Header": "Tester123"})
    assert response.status_code == 200
    assert "x-test-header" in response.json()["headers"]
    assert response.json()["headers"]["x-test-header"] == "Tester123"

# 6. File Uploads Tests
def test_upload_text_file():
    text_data = b"Hello tester. This is a text file upload test.\nLine 2 contents."
    files = {"file": ("test.txt", text_data, "text/plain")}
    response = client.post("/api/v1/upload/text", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["word_count"] == 12
    assert data["line_count"] == 2
    assert "test.txt" == data["filename"]

def test_upload_image_file():
    # Generate 1x1 png image in memory
    img_byte_arr = io.BytesIO()
    image = Image.new('RGB', (100, 100), color = 'red')
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    files = {"file": ("test.png", img_byte_arr, "image/png")}
    response = client.post("/api/v1/upload/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.png"
    assert data["dimensions"]["width"] == 100
    assert data["dimensions"]["height"] == 100
    assert data["format"] == "PNG"

def test_upload_invalid_image():
    files = {"file": ("test.png", b"Not an image at all", "image/png")}
    response = client.post("/api/v1/upload/image", files=files)
    assert response.status_code == 400
    assert "not a valid" in response.json()["detail"].lower()
