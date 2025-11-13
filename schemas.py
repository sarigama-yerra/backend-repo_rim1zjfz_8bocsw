"""
Database Schemas for Art Marketplace & Community

Each Pydantic model below maps to a MongoDB collection using the lowercase
class name as the collection name (e.g., Artwork -> "artwork").

This platform supports:
- Artist profiles and collectors
- Artworks (presented as showcases, purchased via inquiry)
- Supply items (traditional e-commerce flow)
- Community posts with comments and likes
- Orders for supply items
- Inquiries for artwork (conversation starter, not instant checkout)
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class User(BaseModel):
    """
    Users collection schema
    Collection: "user"
    role: "artist" | "collector"
    """
    name: str = Field(..., description="Display name")
    email: EmailStr = Field(..., description="Email address")
    bio: Optional[str] = Field(None, description="Short bio")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    role: str = Field("collector", description="User role: artist or collector")
    instagram: Optional[str] = Field(None, description="Instagram handle")
    website: Optional[str] = Field(None, description="Personal website")
    is_active: bool = Field(True, description="Account active flag")


class Artwork(BaseModel):
    """
    Artwork showcase (not instant checkout). Buyers send inquiries.
    Collection: "artwork"
    """
    title: str = Field(..., description="Artwork title")
    artist_id: str = Field(..., description="Reference to user (artist)")
    description: Optional[str] = Field(None, description="Story behind the piece")
    medium: Optional[str] = Field(None, description="Medium, e.g., Oil on canvas")
    dimensions: Optional[str] = Field(None, description="Size, e.g., 24x36 in")
    year: Optional[int] = Field(None, description="Year created")
    price: Optional[float] = Field(None, ge=0, description="Guide price for inquiries")
    currency: str = Field("USD", description="Currency code")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    is_available: bool = Field(True, description="Available for acquisition")
    location: Optional[str] = Field(None, description="Where the artwork currently is")


class Inquiry(BaseModel):
    """Buyer inquiry about an artwork. Starts a conversation."""
    artwork_id: str = Field(..., description="Artwork being inquired about")
    buyer_id: Optional[str] = Field(None, description="User id of the interested buyer (optional)")
    buyer_name: str = Field(..., description="Name of the inquirer")
    buyer_email: EmailStr = Field(..., description="Contact email")
    message: str = Field(..., description="Message to the artist")
    status: str = Field("open", description="open | responded | closed")


class SupplyItem(BaseModel):
    """Art supplies catalog items (e-commerce)."""
    title: str = Field(..., description="Item name")
    brand: Optional[str] = Field(None, description="Brand")
    description: Optional[str] = Field(None, description="Details")
    price: float = Field(..., ge=0, description="Price")
    currency: str = Field("USD", description="Currency")
    category: str = Field(..., description="Category, e.g., Brushes, Canvas")
    stock: int = Field(0, ge=0, description="Inventory count")
    image_url: Optional[str] = Field(None, description="Image URL")


class OrderItem(BaseModel):
    item_id: str = Field(..., description="SupplyItem id")
    quantity: int = Field(..., ge=1, description="Quantity")


class Order(BaseModel):
    """Order for supply items."""
    buyer_name: str = Field(...)
    buyer_email: EmailStr = Field(...)
    shipping_address: str = Field(...)
    items: List[OrderItem] = Field(...)
    subtotal: float = Field(..., ge=0)
    currency: str = Field("USD")
    status: str = Field("pending", description="pending | paid | shipped | delivered | cancelled")


class Post(BaseModel):
    """Community posts by artists or collectors."""
    author_id: Optional[str] = Field(None, description="User id")
    author_name: str = Field(..., description="Display name shown")
    content: str = Field(..., description="Text content")
    image_url: Optional[str] = Field(None, description="Optional image")
    tags: List[str] = Field(default_factory=list)
    likes: int = Field(0, ge=0)


class Comment(BaseModel):
    post_id: str = Field(...)
    author_name: str = Field(...)
    content: str = Field(...)


# Note: The Flames database viewer will automatically read these via GET /schema
# and use them for validation in the in-app DB viewer.
