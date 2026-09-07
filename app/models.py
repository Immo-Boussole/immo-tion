"""Pydantic schemas and data transfer objects."""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


# ── Properties ────────────────────────────────────────────────────────
class PropertyBase(BaseModel):
    name: str = Field(...)
    address: str = Field(...)
    postal_code: Optional[str] = None
    city: Optional[str] = None
    surface_m2: Optional[float] = None
    land_surface_m2: Optional[float] = None
    cadastral_reference: Optional[str] = None
    dpe_rating: Optional[str] = None
    ges_rating: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[float] = None
    notes: Optional[str] = None
    cover_image: Optional[str] = None


class PropertyCreate(PropertyBase):
    seed_tasks: bool = True


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    surface_m2: Optional[float] = None
    land_surface_m2: Optional[float] = None
    cadastral_reference: Optional[str] = None
    dpe_rating: Optional[str] = None
    ges_rating: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[float] = None
    notes: Optional[str] = None
    cover_image: Optional[str] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ── Maintenance Tasks & Logs ──────────────────────────────────────────
class MaintenanceTaskBase(BaseModel):
    title: str = Field(...)
    category: str = Field(default="Chauffage")
    description: Optional[str] = None
    recurrence_months: int = Field(default=12, ge=1)
    next_due_date: date
    estimated_cost: Optional[float] = None
    preferred_contractor: Optional[str] = None


class MaintenanceTaskCreate(MaintenanceTaskBase):
    property_id: int


class MaintenanceTaskLogCreate(BaseModel):
    performed_date: date
    performed_by: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    update_next_due_date: bool = True


# ── Renovations / Works ────────────────────────────────────────────────
class RenovationCreate(BaseModel):
    property_id: int
    title: str
    category: str = "Général"
    status: str = "Planifié"
    estimated_budget: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    contractor_name: Optional[str] = None
    contractor_siret: Optional[str] = None
    contractor_phone: Optional[str] = None
    contractor_email: Optional[str] = None
    warranty_decennale_expiry: Optional[date] = None
    notes: Optional[str] = None


class RenovationExpenseCreate(BaseModel):
    renovation_id: int
    description: str
    expense_type: str = "Facture"
    amount: float
    date: date
    is_paid: bool = True


# ── Inventory & Equipment ─────────────────────────────────────────────
class InventoryItemCreate(BaseModel):
    property_id: int
    name: str
    brand: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    category: str = "Autre"
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    warranty_expiry_date: Optional[date] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None


# ── Energy Readings ───────────────────────────────────────────────────
class EnergyReadingCreate(BaseModel):
    property_id: int
    energy_type: str = "Électricité"
    reading_date: date
    reading_value: float
    unit: str = "kWh"
    cost: Optional[float] = None
    notes: Optional[str] = None


# ── Immo-Boussole Bridge Import ───────────────────────────────────────
class ImmoBoussoleImportPayload(BaseModel):
    """Payload sent by Immo-Boussole when exporting an acquired property."""
    title: str
    address: str
    postal_code: Optional[str] = None
    city: Optional[str] = None
    surface_m2: Optional[float] = None
    land_surface_m2: Optional[float] = None
    price: Optional[float] = None
    cadastral_reference: Optional[str] = None
    dpe_rating: Optional[str] = None
    ges_rating: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    contacts: List[dict] = Field(default_factory=list)
    furniture_inventory: List[dict] = Field(default_factory=list)
    seed_tasks: bool = True


# ── Users & Authentication ────────────────────────────────────────────
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    role: str = Field(default="user")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    created_at: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str


class SetupStep1Payload(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    confirm_password: str
    email: Optional[str] = None
    default_language: str = Field(default="fr")


class SetupStep2Payload(BaseModel):
    property_name: Optional[str] = None
    property_city: Optional[str] = None
    property_address: Optional[str] = None

