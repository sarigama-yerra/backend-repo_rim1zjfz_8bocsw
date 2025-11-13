import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import User, Artwork, Inquiry, SupplyItem, Order, Post, Comment

app = FastAPI(title="ArtFlow - Marketplace & Community")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "ArtFlow backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# --------- Public Showcase Endpoints (Artworks) ---------

@app.post("/artworks")
def create_artwork(art: Artwork):
    try:
        art_id = create_document("artwork", art)
        return {"id": art_id, "message": "Artwork created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/artworks")
def list_artworks(q: Optional[str] = None, limit: int = 20):
    try:
        filter_dict = {}
        if q:
            # simple text search on title or description
            filter_dict = {"$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"medium": {"$regex": q, "$options": "i"}},
            ]}
        docs = get_documents("artwork", filter_dict, limit)
        # format for showcase cards (no raw checkout)
        formatted = [
            {
                "id": str(d.get("_id")),
                "title": d.get("title"),
                "artist_id": d.get("artist_id"),
                "images": d.get("images", [])[:3],
                "price": d.get("price"),
                "currency": d.get("currency", "USD"),
                "is_available": d.get("is_available", True),
                "medium": d.get("medium"),
                "year": d.get("year"),
            }
            for d in docs
        ]
        return {"items": formatted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InquiryPayload(BaseModel):
    artwork_id: str
    buyer_name: str
    buyer_email: EmailStr
    message: str
    buyer_id: Optional[str] = None


@app.post("/inquiries")
def create_inquiry(payload: InquiryPayload):
    try:
        inquiry = Inquiry(
            artwork_id=payload.artwork_id,
            buyer_id=payload.buyer_id,
            buyer_name=payload.buyer_name,
            buyer_email=payload.buyer_email,
            message=payload.message,
        )
        inquiry_id = create_document("inquiry", inquiry)
        return {"id": inquiry_id, "message": "Inquiry sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------- Supplies Catalog (E-commerce) ---------

@app.post("/supplies")
def create_supply(item: SupplyItem):
    try:
        item_id = create_document("supplyitem", item)
        return {"id": item_id, "message": "Supply item created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/supplies")
def list_supplies(category: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {"category": category} if category else {}
        docs = get_documents("supplyitem", filter_dict, limit)
        formatted = [
            {
                "id": str(d.get("_id")),
                "title": d.get("title"),
                "brand": d.get("brand"),
                "price": d.get("price"),
                "currency": d.get("currency", "USD"),
                "stock": d.get("stock", 0),
                "image_url": d.get("image_url"),
                "category": d.get("category"),
            }
            for d in docs
        ]
        return {"items": formatted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OrderPayload(BaseModel):
    buyer_name: str
    buyer_email: EmailStr
    shipping_address: str
    items: List[dict]
    currency: Optional[str] = "USD"


@app.post("/orders")
def create_order(payload: OrderPayload):
    try:
        # compute subtotal
        subtotal = 0.0
        for it in payload.items:
            qty = int(it.get("quantity", 1))
            price = float(it.get("price", 0))
            subtotal += qty * price
        order = Order(
            buyer_name=payload.buyer_name,
            buyer_email=payload.buyer_email,
            shipping_address=payload.shipping_address,
            items=[{"item_id": i.get("item_id"), "quantity": int(i.get("quantity", 1))} for i in payload.items],
            subtotal=round(subtotal, 2),
            currency=payload.currency or "USD",
        )
        order_id = create_document("order", order)
        return {"id": order_id, "message": "Order placed", "subtotal": order.subtotal}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------- Community (Social) ---------

@app.post("/posts")
def create_post(post: Post):
    try:
        pid = create_document("post", post)
        return {"id": pid, "message": "Post created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts")
def list_posts(limit: int = 20):
    try:
        docs = get_documents("post", {}, limit)
        formatted = [
            {
                "id": str(d.get("_id")),
                "author_name": d.get("author_name"),
                "content": d.get("content"),
                "image_url": d.get("image_url"),
                "tags": d.get("tags", []),
                "likes": d.get("likes", 0),
            }
            for d in docs
        ]
        return {"items": formatted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LikePayload(BaseModel):
    post_id: str


@app.post("/posts/like")
def like_post(payload: LikePayload):
    # Increment likes for a post by its id
    try:
        if db is None:
            raise Exception("Database not available")
        from bson import ObjectId
        try:
            oid = ObjectId(payload.post_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid post id")
        doc = db["post"].find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Post not found")
        likes = int(doc.get("likes", 0)) + 1
        db["post"].update_one({"_id": oid}, {"$set": {"likes": likes}})
        return {"id": payload.post_id, "likes": likes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------- Schema Introspection (for in-app DB viewer) ---------

@app.get("/schema")
def get_schema_definitions():
    # Expose model field names for quick admin/dev viewing
    def model_to_fields(model_cls):
        return list(model_cls.model_fields.keys())

    return {
        "user": model_to_fields(User),
        "artwork": model_to_fields(Artwork),
        "inquiry": model_to_fields(Inquiry),
        "supplyitem": model_to_fields(SupplyItem),
        "order": model_to_fields(Order),
        "post": model_to_fields(Post),
        "comment": model_to_fields(Comment),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
