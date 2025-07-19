"""
Pydantic data models for POC Intake schemas
Based on the JSON schemas: demographics, insurance, weight_history, medical_history
"""

from datetime import date
from typing import List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field


# Enums for standardized values
class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PreferredContactEnum(str, Enum):
    MOBILE = "mobile"
    HOME = "home"
    WORK = "work"


class CommunicationMethodEnum(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    TEXT = "text"
    PORTAL = "portal"


class MaritalStatusEnum(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    OTHER = "Other"


class EmploymentStatusEnum(str, Enum):
    EMPLOYED = "Employed"
    FULL_TIME_STUDENT = "Full-Time Student"
    PART_TIME_STUDENT = "Part-Time Student"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"


class InsuranceTypeEnum(str, Enum):
    MEDICARE = "MEDICARE"
    MEDICAID = "MEDICAID"
    TRICARE = "TRICARE"
    GROUP_HEALTH_PLAN = "GROUP HEALTH PLAN"
    OTHER = "OTHER"


class RelationshipEnum(str, Enum):
    SELF = "Self"
    SPOUSE = "Spouse"
    CHILD = "Child"
    OTHER = "Other"


class SeverityEnum(str, Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"


class TreatmentApproachEnum(str, Enum):
    SURGICAL = "Surgical"
    NON_SURGICAL = "Non-surgical"
    BOTH = "Both"
    UNDECIDED = "Undecided"


# Demographics Models
class PhoneInfo(BaseModel):
    mobile: str = Field(..., max_length=15)
    home: Optional[str] = Field(None, max_length=15)
    work: Optional[str] = Field(None, max_length=15)
    work_extension: Optional[str] = Field(None, max_length=4, alias="workExtension")
    preferred: Optional[PreferredContactEnum] = None


class Address(BaseModel):
    address_line1: str = Field(..., max_length=35, alias="addressLine1")
    address_line2: Optional[str] = Field(None, max_length=35, alias="addressLine2")
    city: str = Field(..., max_length=35)
    state: str = Field(..., max_length=50)
    country: str = Field(default="us", max_length=2)
    zip_code: str = Field(..., max_length=10, alias="zipCode")


class EmergencyContact(BaseModel):
    name: str = Field(..., max_length=70)
    phone: str = Field(..., max_length=10)
    phone_extension: Optional[str] = Field(None, max_length=4, alias="phoneExtension")


class CommunicationPreferences(BaseModel):
    preferred_method: Optional[CommunicationMethodEnum] = Field(None, alias="preferredMethod")
    email_notifications: bool = Field(default=True, alias="emailNotifications")
    text_notifications: bool = Field(default=True, alias="textNotifications")
    voice_notifications: bool = Field(default=True, alias="voiceNotifications")


class AdditionalInfo(BaseModel):
    language: str = Field(default="English", max_length=100)
    marital_status: Optional[MaritalStatusEnum] = Field(None, alias="maritalStatus")
    employment_status: Optional[EmploymentStatusEnum] = Field(None, alias="employmentStatus")


class CareTeamProvider(BaseModel):
    provider_name: Optional[str] = Field(None, alias="providerName")
    phone: Optional[str] = Field(None, max_length=15)
    specialty: Optional[str] = None
    practice_name: Optional[str] = Field(None, alias="practiceName")
    provider_id: Optional[int] = Field(None, alias="providerId")
    relationship_type: Optional[str] = Field(None, alias="relationshipType")
    is_primary_care_physician: Optional[bool] = Field(None, alias="isPrimaryCarePhysician")


class IntakeDemographics(BaseModel):
    first_name: str = Field(..., max_length=35, alias="firstName")
    middle_name: Optional[str] = Field(None, max_length=35, alias="middleName")
    last_name: str = Field(..., max_length=35, alias="lastName")
    date_of_birth: date = Field(..., alias="dateOfBirth")
    gender: GenderEnum
    email: str = Field(..., max_length=100)
    phone: PhoneInfo
    address: Address
    emergency_contact: EmergencyContact = Field(..., alias="emergencyContact")
    communication_preferences: Optional[CommunicationPreferences] = Field(None, alias="communicationPreferences")
    additional_info: Optional[AdditionalInfo] = Field(None, alias="additionalInfo")
    care_team_providers: Optional[List[CareTeamProvider]] = Field(None, alias="careTeamProviders")


# Insurance Models
class PolicyHolder(BaseModel):
    relationship: RelationshipEnum
    first_name: str = Field(..., max_length=35, alias="firstName")
    last_name: str = Field(..., max_length=35, alias="lastName")
    date_of_birth: date = Field(..., alias="dateOfBirth")
    gender: GenderEnum


class InsuranceCards(BaseModel):
    front_image_url: Optional[str] = Field(None, alias="frontImageUrl")
    back_image_url: Optional[str] = Field(None, alias="backImageUrl")


class InsurancePlan(BaseModel):
    insurance_type: InsuranceTypeEnum = Field(..., alias="insuranceType")
    plan_name: Optional[str] = Field(None, max_length=150, alias="planName")
    plan_id: str = Field(..., max_length=30, alias="planId")
    group_number: Optional[str] = Field(None, max_length=30, alias="groupNumber")
    practice_payer_id: Optional[int] = Field(None, alias="practicePayerId")
    payer_name: Optional[str] = Field(None, max_length=150, alias="payerName")
    employer: Optional[str] = Field(None, max_length=150)
    valid_from: Optional[date] = Field(None, alias="validFrom")
    valid_to: Optional[date] = Field(None, alias="validTo")
    policy_holder: PolicyHolder = Field(..., alias="policyHolder")
    insurance_cards: Optional[InsuranceCards] = Field(None, alias="insuranceCards")


class SecondaryInsurance(BaseModel):
    has_secondary: Optional[bool] = Field(None, alias="hasSecondary")
    insurance_type: Optional[InsuranceTypeEnum] = Field(None, alias="insuranceType")
    plan_name: Optional[str] = Field(None, max_length=150, alias="planName")
    plan_id: Optional[str] = Field(None, max_length=30, alias="planId")
    group_number: Optional[str] = Field(None, max_length=30, alias="groupNumber")
    payer_name: Optional[str] = Field(None, max_length=150, alias="payerName")
    policy_holder: Optional[PolicyHolder] = Field(None, alias="policyHolder")
    insurance_cards: Optional[InsuranceCards] = Field(None, alias="insuranceCards")


class PharmacyCard(BaseModel):
    has_separate_pharmacy: Optional[bool] = Field(None, alias="hasSeparatePharmacy")
    front_image_url: Optional[str] = Field(None, alias="frontImageUrl")
    back_image_url: Optional[str] = Field(None, alias="backImageUrl")


class DriversLicense(BaseModel):
    has_drivers_license: Optional[bool] = Field(None, alias="hasDriversLicense")
    image_url: Optional[str] = Field(None, alias="imageUrl")


class IdentificationDocuments(BaseModel):
    drivers_license: Optional[DriversLicense] = Field(None, alias="driversLicense")


class IntakeInsurance(BaseModel):
    primary_insurance: InsurancePlan = Field(..., alias="primaryInsurance")
    secondary_insurance: Optional[SecondaryInsurance] = Field(None, alias="secondaryInsurance")
    pharmacy_card: Optional[PharmacyCard] = Field(None, alias="pharmacyCard")
    identification_documents: Optional[IdentificationDocuments] = Field(None, alias="identificationDocuments")


# Weight History Models
class Height(BaseModel):
    feet: int
    inches: int


class CurrentVitals(BaseModel):
    height: Height
    weight: float


class WeightHistory(BaseModel):
    max_ever_weighed: Optional[float] = Field(None, alias="maxEverWeighed")
    age_at_max_weight: Optional[int] = Field(None, alias="ageAtMaxWeight")
    max_weight_lost_by_dieting: Optional[float] = Field(None, alias="maxWeightLostByDieting")


class WeightGainFactors(BaseModel):
    weight_gaining_medications: Optional[str] = Field(None, alias="weightGainingMedications")
    injuries: Optional[str] = None
    chronic_stress_or_depression: Optional[str] = Field(None, alias="chronicStressOrDepression")
    processed_food_addictions: Optional[str] = Field(None, alias="processedFoodAddictions")
    pregnancy: Optional[str] = None
    menopause: Optional[str] = None
    sugar_containing_beverages: Optional[str] = Field(None, alias="sugarContainingBeverages")
    alcohol: Optional[str] = None
    artificial_sweetener: Optional[str] = Field(None, alias="artificialSweetener")
    quitting_smoking: Optional[str] = Field(None, alias="quittingSmoking")
    genetics: Optional[str] = None
    night_shift_work: Optional[str] = Field(None, alias="nightShiftWork")
    childhood_trauma: Optional[str] = Field(None, alias="childhoodTrauma")


class TypicalDayEating(BaseModel):
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None
    snacks_desserts: Optional[str] = Field(None, alias="snacksDesserts")
    beverages: Optional[str] = None


class DietHistory(BaseModel):
    past_diets_tried: Optional[List[str]] = Field(None, alias="pastDietsTried")
    weight_gain_factors: Optional[WeightGainFactors] = Field(None, alias="weightGainFactors")
    struggles_with_diet: Optional[List[str]] = Field(None, alias="strugglesWithDiet")
    typical_day_eating: Optional[TypicalDayEating] = Field(None, alias="typicalDayEating")


class GLP1Medication(BaseModel):
    has_tried: Optional[bool] = Field(None, alias="hasTried")
    brand_names: Optional[List[str]] = Field(None, alias="brandNames")
    highest_dose: Optional[str] = Field(None, alias="highestDose")
    treatment_duration: Optional[str] = Field(None, alias="treatmentDuration")
    weight_lost: Optional[float] = Field(None, alias="weightLost")


class GLP1Medications(BaseModel):
    has_tried_glp1: Optional[bool] = Field(None, alias="hasTriedGlp1")
    tirzepatide: Optional[GLP1Medication] = None
    semaglutide: Optional[GLP1Medication] = None


class WeightLossMedicationHistory(BaseModel):
    glp1_medications: Optional[GLP1Medications] = Field(None, alias="glp1Medications")
    other_weight_loss_medications: Optional[List[str]] = Field(None, alias="otherWeightLossMedications")


class BariatricSurgeryHistory(BaseModel):
    has_bariatric_surgery_history: Optional[bool] = Field(None, alias="hasBariatricSurgeryHistory")
    surgery_year: Optional[int] = Field(None, alias="surgeryYear")
    surgery_type: Optional[List[str]] = Field(None, alias="surgeryType")
    pre_surgery_weight: Optional[float] = Field(None, alias="preSurgeryWeight")
    lowest_weight_after_surgery: Optional[float] = Field(None, alias="lowestWeightAfterSurgery")


class TreatmentPreferences(BaseModel):
    treatment_approach: Optional[TreatmentApproachEnum] = Field(None, alias="treatmentApproach")


class IntakeWeightHistory(BaseModel):
    current_vitals: CurrentVitals = Field(..., alias="currentVitals")
    weight_history: Optional[WeightHistory] = Field(None, alias="weightHistory")
    diet_history: Optional[DietHistory] = Field(None, alias="dietHistory")
    exercise_information: Optional[str] = Field(None, alias="exerciseInformation")
    weight_loss_medication_history: Optional[WeightLossMedicationHistory] = Field(None, alias="weightLossMedicationHistory")
    bariatric_surgery_history: Optional[BariatricSurgeryHistory] = Field(None, alias="bariatricSurgeryHistory")
    treatment_preferences: Optional[TreatmentPreferences] = Field(None, alias="treatmentPreferences")


# Medical History Models
class Medication(BaseModel):
    medication_name: Optional[str] = Field(None, alias="medicationName")
    strength: Optional[str] = None
    directions: Optional[str] = None


class Allergy(BaseModel):
    allergen: Optional[str] = None
    reaction: Optional[str] = None
    severity: Optional[SeverityEnum] = None


class FamilyHistoryItem(BaseModel):
    family_member: str = Field(..., alias="familyMember")
    medical_problem: str = Field(..., alias="medicalProblem")


class PastSurgery(BaseModel):
    surgery_type: str = Field(..., alias="surgeryType")
    year: int


class GERDHeartburn(BaseModel):
    has_gerd: Optional[bool] = Field(None, alias="hasGerd")
    gerd_details: Optional[str] = Field(None, alias="gerdDetails")


class Pancreatitis(BaseModel):
    has_pancreatitis: Optional[bool] = Field(None, alias="hasPancreatitis")
    number_of_attacks: Optional[int] = Field(None, alias="numberOfAttacks")
    cause: Optional[str] = None


class SpecificConditions(BaseModel):
    gerd_heartburn: Optional[GERDHeartburn] = Field(None, alias="gerdHeartburn")
    pancreatitis: Optional[Pancreatitis] = None


class SocialHistory(BaseModel):
    smoking_summary: str = Field(..., alias="smokingSummary")
    alcohol_summary: str = Field(..., alias="alcoholSummary")
    marijuana_summary: Optional[str] = Field(None, alias="marijuanaSummary")
    drug_summary: str = Field(..., alias="drugSummary")
    employment_status: Optional[EmploymentStatusEnum] = Field(None, alias="employmentStatus")
    financial_situation: Optional[str] = Field(None, alias="financialSituation")
    employment_details: Optional[str] = Field(None, alias="employmentDetails")
    education_background: Optional[str] = Field(None, alias="educationBackground")


class IntakeMedicalHistory(BaseModel):
    current_medications: Optional[List[Medication]] = Field(None, alias="currentMedications")
    allergies: Optional[List[Allergy]] = None
    pmhx: Optional[List[str]] = Field(None, alias="PMHx")
    pmhx_obesity_comorbid: Optional[List[str]] = Field(None, alias="PMHxObesityComorbid")
    family_history: Optional[List[FamilyHistoryItem]] = Field(None, alias="familyHistory")
    past_surgical_history: Optional[List[PastSurgery]] = Field(None, alias="pastSurgicalHistory")
    specific_conditions: Optional[SpecificConditions] = Field(None, alias="specificConditions")
    social_history: SocialHistory = Field(..., alias="socialHistory")


# Main Intake Session Model
class IntakeSession(BaseModel):
    """Complete intake session containing all four schema sections"""
    intake_demographics: Optional[IntakeDemographics] = Field(None, alias="intake_demographics")
    intake_insurance: Optional[IntakeInsurance] = Field(None, alias="intake_insurance")
    intake_weight_history: Optional[IntakeWeightHistory] = Field(None, alias="intake_weight_history")
    intake_medical_history: Optional[IntakeMedicalHistory] = Field(None, alias="intake_medical_history")
    completed: bool = False
    session_id: Optional[str] = None
    patient_mrn: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None