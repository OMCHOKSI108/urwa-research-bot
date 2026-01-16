"""
Dynamic data schemas for different types of scraped content.
The LLM determines which schema fits the data and structures it accordingly.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DataSchemaType(str, Enum):
    """Types of data schemas available"""
    COMPANY = "company"
    PRODUCT = "product"
    ARTICLE = "article"
    PERSON = "person"
    JOB = "job"
    RECIPE = "recipe"
    EVENT = "event"
    REVIEW = "review"
    PLACE = "place"
    GENERIC = "generic"


# ===== COMPANY SCHEMA =====
class CompanyData(BaseModel):
    name: str
    rating: Optional[str] = None
    reviews_count: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    founded: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")  # Allow additional fields


# ===== PRODUCT SCHEMA =====
class ProductData(BaseModel):
    name: str
    price: Optional[str] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[str] = None
    reviews_count: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== ARTICLE SCHEMA =====
class ArticleData(BaseModel):
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    read_time: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== PERSON SCHEMA =====
class PersonData(BaseModel):
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    bio: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== JOB SCHEMA =====
class JobData(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract
    experience: Optional[str] = None
    posted_date: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== RECIPE SCHEMA =====
class RecipeData(BaseModel):
    name: str
    cuisine: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    servings: Optional[str] = None
    difficulty: Optional[str] = None
    rating: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== EVENT SCHEMA =====
class EventData(BaseModel):
    name: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    registration_url: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== REVIEW SCHEMA =====
class ReviewData(BaseModel):
    title: str
    rating: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    verified: Optional[bool] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    content: Optional[str] = None
    helpful_count: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== PLACE SCHEMA =====
class PlaceData(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


# ===== GENERIC SCHEMA (fallback) =====
class GenericData(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="allow")


# Schema mapping
SCHEMA_MAP = {
    DataSchemaType.COMPANY: CompanyData,
    DataSchemaType.PRODUCT: ProductData,
    DataSchemaType.ARTICLE: ArticleData,
    DataSchemaType.PERSON: PersonData,
    DataSchemaType.JOB: JobData,
    DataSchemaType.RECIPE: RecipeData,
    DataSchemaType.EVENT: EventData,
    DataSchemaType.REVIEW: ReviewData,
    DataSchemaType.PLACE: PlaceData,
    DataSchemaType.GENERIC: GenericData,
}


class StructuredDataResponse(BaseModel):
    """Response with auto-detected schema"""
    schema_type: DataSchemaType
    schema_confidence: str  # low, medium, high
    total_items: int
    data: List[Dict[str, Any]]  # Actual structured data
    schema_fields: List[str]  # Fields in the schema
    
    model_config = ConfigDict(extra="allow")
