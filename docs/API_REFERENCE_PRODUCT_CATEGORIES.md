# Product Categories API Reference

## Base URL
```
/api/product-categories
```

## Endpoints

### 1. Create Product Category

**POST** `/api/product-categories`

Creates a new product category.

**Request Body:**
```json
{
  "name": "Busts",
  "description": "Character busts and head sculptures"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Busts",
  "description": "Character busts and head sculptures",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

**Validation:**
- `name` is required and cannot be empty
- `description` is optional

**Error Responses:**
- `400 Bad Request` - Invalid input (e.g., empty name)

---

### 2. List All Product Categories

**GET** `/api/product-categories`

Retrieves all product categories.

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Busts",
    "description": "Character busts and head sculptures",
    "created_at": "2025-11-24T10:30:00Z",
    "updated_at": "2025-11-24T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Full Format Figures",
    "description": "Complete miniature figures",
    "created_at": "2025-11-24T10:31:00Z",
    "updated_at": "2025-11-24T10:31:00Z"
  }
]
```

---

### 3. Get Product Category by ID

**GET** `/api/product-categories/{category_id}`

Retrieves a specific product category by its ID.

**Path Parameters:**
- `category_id` (UUID) - The unique identifier of the category

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Busts",
  "description": "Character busts and head sculptures",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Category with specified ID doesn't exist

---

### 4. Update Product Category

**PUT** `/api/product-categories/{category_id}`

Updates an existing product category. Supports partial updates.

**Path Parameters:**
- `category_id` (UUID) - The unique identifier of the category

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

Both fields are optional. Only provided fields will be updated.

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Name",
  "description": "Updated description",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T11:00:00Z"
}
```

**Validation:**
- If `name` is provided, it cannot be empty

**Error Responses:**
- `400 Bad Request` - Invalid input (e.g., empty name)
- `404 Not Found` - Category with specified ID doesn't exist

---

### 5. Delete Product Category

**DELETE** `/api/product-categories/{category_id}`

Deletes a product category.

**Path Parameters:**
- `category_id` (UUID) - The unique identifier of the category

**Response:** `204 No Content`

No response body.

**Error Responses:**
- `404 Not Found` - Category with specified ID doesn't exist

---

## Example Usage

### Using cURL

```bash
# Create a category
curl -X POST http://localhost:8000/api/product-categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Busts", "description": "Character busts"}'

# List all categories
curl http://localhost:8000/api/product-categories

# Get specific category
curl http://localhost:8000/api/product-categories/{category_id}

# Update category
curl -X PUT http://localhost:8000/api/product-categories/{category_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Delete category
curl -X DELETE http://localhost:8000/api/product-categories/{category_id}
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api/product-categories"

# Create
response = requests.post(BASE_URL, json={
    "name": "Busts",
    "description": "Character busts"
})
category = response.json()

# List all
response = requests.get(BASE_URL)
categories = response.json()

# Get by ID
category_id = category["id"]
response = requests.get(f"{BASE_URL}/{category_id}")

# Update
response = requests.put(f"{BASE_URL}/{category_id}", json={
    "description": "Updated description"
})

# Delete
response = requests.delete(f"{BASE_URL}/{category_id}")
```

---

## Data Model

### ProductCategory

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Auto-generated | Unique identifier |
| name | string | Yes | Category name (max 255 chars) |
| description | string | No | Category description (max 1000 chars) |
| created_at | datetime | Auto-generated | Creation timestamp |
| updated_at | datetime | Auto-generated | Last update timestamp |

---

## Related Endpoints

Product categories are used by:
- Product management (`/api/products`)
- Order items (for categorizing products in orders)

---

## Notes

- All timestamps are in UTC
- UUIDs are returned as strings
- The API uses JSON for all request and response bodies
- Content-Type header should be `application/json` for POST and PUT requests
