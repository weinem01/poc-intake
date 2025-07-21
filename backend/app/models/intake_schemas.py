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
    mobile: str = Field(..., max_length=15, question_group=2, description="AI Agent: Ask 'What is your mobile phone number?'")# type: ignore
    home: Optional[str] = Field(None, max_length=15, question_group=3, description="AI Agent: Ask 'Do you have a home phone number?'")# type: ignore
    work: Optional[str] = Field(None, max_length=15, question_group=3, description="AI Agent: Ask 'Do you want to provide a work phone number?'")# type: ignore
    preferred: Optional[PreferredContactEnum] = Field(None, question_group=3, description="AI Agent: Ask 'Which phone number would you prefer us to contact you on?' Options: mobile, home, work, only if there is more than one phone number, otherwise choose mobile")# type: ignore


class Address(BaseModel):
    address_line1: str = Field(..., max_length=35, alias="addressLine1", question_group=4, description="AI Agent: Ask 'What is your home address?' If the patient adds more than their street address, review the response and use it to populate the remaining address fields")# type: ignore
    # address_line2: Optional[str] = Field(None, max_length=35, alias="addressLine2", question_group=4, description="AI Agent: Ask 'Do you have an apartment, suite, or unit number?' (Optional)")# type: ignore
    city: str = Field(..., max_length=35, question_group=4, description="AI Agent: Ask 'What city do you live in?'")# type: ignore
    state: str = Field(..., max_length=50, question_group=4, description="AI Agent: Ask 'What state do you live in?'")# type: ignore
    zip_code: str = Field(..., max_length=10, alias="zipCode", question_group=4, description="AI Agent: Ask 'What is your ZIP code?'")# type: ignore
    country: str = Field(default="us", max_length=2, question_group=4, description="AI Agent: Country code - defaults to 'us' for United States. Only ask if address format suggests international (postal codes with letters, unusual formats).")# type: ignore


class EmergencyContact(BaseModel):
    name: str = Field(..., max_length=70, question_group=5, description="AI Agent: Ask 'Who should we contact in case of an emergency? Can you also provide a phone number and relationship?'")# type: ignore
    phone: str = Field(..., max_length=10, question_group=5, description="AI Agent: Ask 'What is their phone number?'") # type: ignore
    relationship: Optional[str] = Field(None, max_length=35, question_group=5, description="AI Agent: Ask 'What is their relationship to you?'")# type: ignore


class CommunicationPreferences(BaseModel):
    preferred_method: Optional[CommunicationMethodEnum] = Field(None, alias="preferredMethod", question_group=7, description="AI Agent: Ask 'How would you prefer to receive important communications from us?' Options: email, phone, text, portal")# type: ignore
    email_notifications: bool = Field(default=True, alias="emailNotifications", question_group=7, description="AI Agent: Ask 'Would you like to receive email notifications?' Default: True")# type: ignore
    text_notifications: bool = Field(default=True, alias="textNotifications", question_group=7, description="AI Agent: Ask 'Would you like to receive text message notifications?' Default: True")# type: ignore
    voice_notifications: bool = Field(default=True, alias="voiceNotifications", question_group=7, description="AI Agent: Ask 'Would you like to receive voice call notifications?' Default: True")# type: ignore


# Removed AdditionalInfo class - fields moved to IntakeDemographics directly


class CareTeamProvider(BaseModel):
    provider_name: Optional[str] = Field(None, alias="providerName", question_group=8, description="AI Agent: Ask 'Would you like to provide the name of any of your doctors or other healthcare providers?'")# type: ignore
    phone: Optional[str] = Field(None, max_length=15, question_group=8, description="AI Agent: Ask 'What is this provider's phone number?'")# type: ignore
    provider_id: Optional[int] = Field(None, alias="providerId", description="This is never asked to the user, instead, use the search_providers tool to get the provider ID using the provider name and phone number. No need to gather additional data if a match is found")# type: ignore
    specialty: Optional[str] = Field(None, question_group=8, description="AI Agent: Ask 'What is this provider's specialty?' If the provider is a pcp, specialty should be left empty and not asked about unless the user volunteers a specialty")# type: ignore
    practice_name: Optional[str] = Field(None, alias="practiceName", question_group=8, description="AI Agent: Ask 'What is the name of their practice or clinic?'")# type: ignore
    relationship_type: Optional[str] = Field(None, alias="relationshipType", question_group=8, description="AI Agent: Ask 'What type of care do they provide you?'")# type: ignore
    is_primary_care_physician: Optional[bool] = Field(None, alias="isPrimaryCarePhysician", question_group=8, description="AI Agent: Ask 'Is this your primary care physician?' Yes/No question")# type: ignore


class IntakeDemographics(BaseModel):
    # Group 1: Basic Personal Information (already have most from EHR)
    first_name: str = Field(..., max_length=35, alias="firstName", question_group=1, description="AI Agent: Ask 'What is your first name?'")# type: ignore
    middle_name: Optional[str] = Field(None, max_length=35, alias="middleName", question_group=1, description="AI Agent: Ask 'What is your middle name?'")# type: ignore
    last_name: str = Field(..., max_length=35, alias="lastName", question_group=1, description="AI Agent: Ask 'What is your last name?'")# type: ignore
    date_of_birth: date = Field(..., alias="dateOfBirth", question_group=1, description="AI Agent: Ask 'What is your date of birth?'")# type: ignore
    gender: GenderEnum = Field(..., question_group=1, description="AI Agent: Ask 'What is your gender?' Options: male, female, other, unknown")# type: ignore
    
    # Group 2: Essential Contact Information
    email: str = Field(..., max_length=100, question_group=2, description="AI Agent: Ask 'What is your email address?'")# type: ignore
    phone: PhoneInfo = Field(..., question_group=2, description="AI Agent: 'What is your phone number?' Collect mobile first (group 2), then optional home/work phones (group 3)")# type: ignore
    
    # Group 4: Address Information
    address: Address = Field(..., question_group=4, description="AI Agent: Collect home address information")# type: ignore
    
    # Group 5: Emergency Contact
    emergency_contact: EmergencyContact = Field(..., alias="emergencyContact", question_group=5, description="AI Agent: Collect emergency contact information")# type: ignore
    
    # Group 6: Personal Details
    marital_status: Optional[MaritalStatusEnum] = Field(None, alias="maritalStatus", question_group=6, description="AI Agent: Ask 'What is your marital status?' Single, Married, Other?")# type: ignore
    employment_status: Optional[EmploymentStatusEnum] = Field(None, alias="employmentStatus", question_group=6, description="AI Agent: Ask 'What is your employment status?' Employed, Full-Time Student, Part-Time Student, Unemployed, Retired")# type: ignore
    
    # Group 7: Communication Preferences  
    communication_preferences: Optional[CommunicationPreferences] = Field(None, alias="communicationPreferences", question_group=7, description="AI Agent: Ask about communication preferences (Optional)")# type: ignore
    
    # Group 8: Healthcare Providers (complex workflow)
    care_team_providers: Optional[List[CareTeamProvider]] = Field(None, alias="careTeamProviders", question_group=8, description="AI Agent: Ask 'Do you have any current healthcare providers we should know about?' Based on the user's input, use the search_providers endpoint to get the provider ID and populate the care team provider information. If an existing provider can be found, return the details of that provider to the user to confirm that this is the correct provider. If no provider can be found on the search_providers tool, use the web search tool to try to find the provider, using the user's city and state as additioanl search terms to improve the accuracy of the search. Also, the user can enter a list of providers, so after adding a provider, be sure to ask if there are any additional providers that they'd like to add. If no providers are provided, this field can be None.")# type: ignore
    
    # System field (not asked)
    is_complete: bool = Field(default=False, alias="isComplete", description="System field: Indicates if this demographics section has been completed. Default: False")


# Insurance Models - COMMENTED OUT FOR TESTING
# # class PolicyHolder(BaseModel):
#     relationship: RelationshipEnum = Field(
#         ...,
#         description="AI Agent: Ask 'What is your relationship to the policy holder?' Options: Self, Spouse, Child, Other"
#     )
#     first_name: str = Field(
#         ..., 
#         max_length=35, 
#         alias="firstName",
#         description="AI Agent: Ask 'What is the policy holder's first name?'"
#     )
#     last_name: str = Field(
#         ..., 
#         max_length=35, 
#         alias="lastName",
#         description="AI Agent: Ask 'What is the policy holder's last name?'"
#     )
#     date_of_birth: date = Field(
#         ..., 
#         alias="dateOfBirth",
#         description="AI Agent: Ask 'What is the policy holder's date of birth?' Format as YYYY-MM-DD"
#     )
#     gender: GenderEnum = Field(
#         ...,
#         description="AI Agent: Ask 'What is the policy holder's gender?' Options: Male, Female, Other"
#     )
# 
# 
# class InsuranceCards(BaseModel):
#     front_image_url: Optional[str] = Field(None, alias="frontImageUrl")
#     back_image_url: Optional[str] = Field(None, alias="backImageUrl")
# 
# 
# class InsurancePlan(BaseModel):
#     insurance_type: InsuranceTypeEnum = Field(
#         ..., 
#         alias="insuranceType",
#         description="AI Agent: Ask 'What type of insurance do you have?' Options: Medicare, Medicaid, Tricare, Group Health Plan, or Other"
#     )
#     plan_name: Optional[str] = Field(
#         None, 
#         max_length=150, 
#         alias="planName",
#         description="AI Agent: Ask 'What is the name of your insurance plan?' (e.g., Blue Cross Blue Shield PPO, Aetna HMO, etc.)"
#     )
#     member_id: str = Field(
#         ..., 
#         max_length=30, 
#         alias="memberId",
#         description="AI Agent: Ask 'What is your member ID or policy number as shown on your insurance card?' Note: This is also called subscriber ID - they are the same thing"
#     )
#     group_number: Optional[str] = Field(
#         None, 
#         max_length=30, 
#         alias="groupNumber",
#         description="AI Agent: Ask 'What is your group number from your insurance card?' This is usually found on the front of the card"
#     )
#     practice_payer_id: Optional[int] = Field(None, alias="practicePayerId")
#     payer_name: Optional[str] = Field(
#         None, 
#         max_length=150, 
#         alias="payerName",
#         description="AI Agent: Ask 'Who is your insurance provider?' (e.g., Blue Cross Blue Shield, UnitedHealthcare, Aetna, Cigna, etc.)"
#     )
#     employer: Optional[str] = Field(
#         None, 
#         max_length=150,
#         description="AI Agent: Ask 'What is the name of your employer or the organization that provides your insurance?' Only ask if insurance_type is GROUP_HEALTH_PLAN"
#     )
#     valid_from: Optional[date] = Field(
#         None, 
#         alias="validFrom",
#         description="AI Agent: Ask 'When did your insurance coverage start?' Format as YYYY-MM-DD"
#     )
#     valid_to: Optional[date] = Field(
#         None, 
#         alias="validTo",
#         description="AI Agent: Ask 'When does your insurance coverage end or expire?' Format as YYYY-MM-DD. Optional field"
#     )
#     policy_holder: PolicyHolder = Field(
#         ..., 
#         alias="policyHolder",
#         description="AI Agent: Ask for policy holder information - who the insurance policy belongs to"
#     )
#     insurance_cards: Optional[InsuranceCards] = Field(
#         None, 
#         alias="insuranceCards",
#         description="AI Agent: Ask 'Can you upload photos of the front and back of your insurance card?' Optional but helpful for verification"
#     )
# 
# 
# class SecondaryInsurance(BaseModel):
#     has_secondary: Optional[bool] = Field(
#         None, 
#         alias="hasSecondary",
#         description="AI Agent: Ask 'Do you have a secondary insurance plan?' Yes/No question"
#     )
#     insurance_type: Optional[InsuranceTypeEnum] = Field(
#         None, 
#         alias="insuranceType",
#         description="AI Agent: If has_secondary is True, ask 'What type of secondary insurance do you have?' Options: Medicare, Medicaid, Tricare, Group Health Plan, or Other"
#     )
#     plan_name: Optional[str] = Field(
#         None, 
#         max_length=150, 
#         alias="planName",
#         description="AI Agent: Ask 'What is the name of your secondary insurance plan?'"
#     )
#     member_id: Optional[str] = Field(
#         None, 
#         max_length=30, 
#         alias="memberId",
#         description="AI Agent: Ask 'What is your member ID for your secondary insurance?'"
#     )
#     group_number: Optional[str] = Field(
#         None, 
#         max_length=30, 
#         alias="groupNumber",
#         description="AI Agent: Ask 'What is your group number for your secondary insurance?'"
#     )
#     payer_name: Optional[str] = Field(
#         None, 
#         max_length=150, 
#         alias="payerName",
#         description="AI Agent: Ask 'Who is your secondary insurance provider?'"
#     )
#     policy_holder: Optional[PolicyHolder] = Field(
#         None, 
#         alias="policyHolder",
#         description="AI Agent: Ask for secondary insurance policy holder information"
#     )
#     insurance_cards: Optional[InsuranceCards] = Field(
#         None, 
#         alias="insuranceCards",
#         description="AI Agent: Ask 'Can you upload photos of your secondary insurance card?'"
#     )
# 
# 
# class PharmacyCard(BaseModel):
#     has_separate_pharmacy: Optional[bool] = Field(None, alias="hasSeparatePharmacy", description="AI Agent: Ask 'Do you have a separate pharmacy card?' Yes/No question (Optional)")
#     front_image_url: Optional[str] = Field(None, alias="frontImageUrl", description="AI Agent: Ask 'Can you upload a photo of the front of your pharmacy card?' (Optional)")
#     back_image_url: Optional[str] = Field(None, alias="backImageUrl", description="AI Agent: Ask 'Can you upload a photo of the back of your pharmacy card?' (Optional)")
# 
# 
# class DriversLicense(BaseModel):
#     has_drivers_license: Optional[bool] = Field(None, alias="hasDriversLicense", description="AI Agent: Ask 'Do you have a driver's license for identification?' Yes/No question (Optional)")
#     image_url: Optional[str] = Field(None, alias="imageUrl", description="AI Agent: Ask 'Can you upload a photo of your driver's license?' (Optional)")
# 
# 
# class IdentificationDocuments(BaseModel):
#     drivers_license: Optional[DriversLicense] = Field(None, alias="driversLicense", description="AI Agent: Collect driver's license information for identification (Optional)")
# 
# 
# class IntakeInsurance(BaseModel):
#     primary_insurance: InsurancePlan = Field(..., alias="primaryInsurance", description="AI Agent: Collect primary insurance information")
#     secondary_insurance: Optional[SecondaryInsurance] = Field(None, alias="secondaryInsurance", description="AI Agent: Collect secondary insurance information if applicable (Optional)")
#     pharmacy_card: Optional[PharmacyCard] = Field(None, alias="pharmacyCard", description="AI Agent: Collect pharmacy card information if applicable (Optional)")
#     identification_documents: Optional[IdentificationDocuments] = Field(None, alias="identificationDocuments", description="AI Agent: Collect identification documents like driver's license (Optional)")


# Weight History Models
class Height(BaseModel):
    feet: int = Field(..., description="AI Agent: Ask 'How tall are you?' Extract feet and inches from the response")
    inches: int = Field(..., description="AI Agent: Ask 'How many additional inches?'")


class CurrentVitals(BaseModel):
    height: Height = Field(..., description="AI Agent: Collect current height information")
    weight: float = Field(..., description="AI Agent: Ask 'What is your current weight in pounds?'")


class WeightHistory(BaseModel):
    max_ever_weighed: Optional[float] = Field(None, alias="maxEverWeighed", description="AI Agent: Ask 'What is the most you have ever weighed?' Specify that they should exclude pregnancy weight if they are female")
    age_at_max_weight: Optional[int] = Field(None, alias="ageAtMaxWeight", description="AI Agent: Ask 'How old were you when you weighed the most?'")
    max_weight_lost_by_dieting: Optional[float] = Field(None, alias="maxWeightLostByDieting", description="AI Agent: Ask 'What is the most weight you have ever lost through dieting?'")


class WeightGainFactors(BaseModel):
    weight_gaining_medications: Optional[str] = Field(None, alias="weightGainingMedications", description="AI Agent: Ask 'Let's discuss things that have caused your weight gain, Have you taken any medications that may have caused weight gain? Please list as many factors as you can including injuries, chronic stress, depression, food addictions, pregnancy, menopause, sugary beverages, alcohol, artificial sweeteners, quitting smoking, genetics, night shift work, and childhood trauma.'")
    injuries: Optional[str] = Field(None, description="AI Agent: Ask 'Have you had any injuries that affected your activity level or weight?'")
    chronic_stress_or_depression: Optional[str] = Field(None, alias="chronicStressOrDepression", description="AI Agent: Ask 'Have you experienced chronic stress or depression that affected your weight?'")
    processed_food_addictions: Optional[str] = Field(None, alias="processedFoodAddictions", description="AI Agent: Ask 'Do you struggle with cravings for processed foods?'")
    pregnancy: Optional[str] = Field(None, description="AI Agent: Ask 'Has pregnancy affected your weight?' Only ask if gender=female")
    menopause: Optional[str] = Field(None, description="AI Agent: Ask 'Has menopause affected your weight?' Only ask if gender=female")
    sugar_containing_beverages: Optional[str] = Field(None, alias="sugarContainingBeverages", description="AI Agent: Ask 'Do you regularly drink sugary beverages like soda, sugary coffee drinks, sweet tea, fruit juice or other beverages that contain sugar?'")
    alcohol: Optional[str] = Field(None, description="AI Agent: Ask 'Has alcohol consumption affected your weight?'")
    artificial_sweetener: Optional[str] = Field(None, alias="artificialSweetener", description="AI Agent: Ask 'Do you use artificial sweeteners regularly?'")
    quitting_smoking: Optional[str] = Field(None, alias="quittingSmoking", description="AI Agent: Ask 'Did you gain weight after quitting smoking?'")
    genetics: Optional[str] = Field(None, description="AI Agent: Ask 'Do you have a family history of obesity?'")
    night_shift_work: Optional[str] = Field(None, alias="nightShiftWork", description="AI Agent: Ask 'Do you work night shifts or have you ever in the past?'")
    childhood_trauma: Optional[str] = Field(None, alias="childhoodTrauma", description="AI Agent: Ask 'Did childhood experiences affect your relationship with food?'")


class TypicalDayEating(BaseModel):
    breakfast: Optional[str] = Field(None, description="AI Agent: Ask 'Tell me about a typical day of eating, go through each meal and also include beverages and snacks.'")
    lunch: Optional[str] = Field(None, description="AI Agent: Ask 'What do you typically eat for lunch?'")
    dinner: Optional[str] = Field(None, description="AI Agent: Ask 'What do you typically eat for dinner?'")
    snacks_desserts: Optional[str] = Field(None, alias="snacksDesserts", description="AI Agent: Ask 'What snacks or desserts do you typically eat?'")
    beverages: Optional[str] = Field(None, description="AI Agent: Ask 'What do you typically drink throughout the day?'")


class DietHistory(BaseModel):
    past_diets_tried: Optional[List[str]] = Field(None, alias="pastDietsTried", description="AI Agent: Ask 'What diets have you tried in the past?' Examples: ['Keto', 'Weight Watchers', 'Low carb', 'Intermittent fasting'] (Optional)")
    weight_gain_factors: Optional[WeightGainFactors] = Field(None, alias="weightGainFactors", description="AI Agent: Collect information about factors that may have contributed to weight gain (Optional)")
    struggles_with_diet: Optional[List[str]] = Field(None, alias="strugglesWithDiet", description="AI Agent: Ask 'What are your biggest challenges with dieting?' Examples: ['Portion control', 'Late night eating', 'Emotional eating'] (Optional)")
    typical_day_eating: Optional[TypicalDayEating] = Field(None, alias="typicalDayEating", description="AI Agent: Collect information about typical daily eating patterns (Optional)")


class GLP1Medication(BaseModel):
    has_tried: Optional[bool] = Field(None, alias="hasTried", description="AI Agent: Ask 'Have you tried this type of GLP-1 medication?' Yes/No question")
    brand_names: Optional[List[str]] = Field(None, alias="brandNames", description="AI Agent: Ask 'What brand names have you used?' Examples: ['Ozempic', 'Wegovy', 'Mounjaro'] (Optional)")
    highest_dose: Optional[str] = Field(None, alias="highestDose", description="AI Agent: Ask 'What was the highest dose you reached?'")
    treatment_duration: Optional[str] = Field(None, alias="treatmentDuration", description="AI Agent: Ask 'How long did you use this medication?'")
    weight_lost: Optional[float] = Field(None, alias="weightLost", description="AI Agent: Ask 'How much weight did you lose on this medication?'")


class GLP1Medications(BaseModel):
    has_tried_glp1: Optional[bool] = Field(None, alias="hasTriedGlp1", description="AI Agent: Ask 'Have you ever tried GLP-1 medications for weight loss? What was the highest dose that you took, how much weight did you lose ont the medication?' Yes/No question")
    tirzepatide: Optional[GLP1Medication] = Field(None, description="AI Agent: If they've tried tirzepatide (Mounjaro, Zepbound), collect details (Optional)")
    semaglutide: Optional[GLP1Medication] = Field(None, description="AI Agent: If they've tried semaglutide (Ozempic, Wegovy), collect details (Optional)")


class WeightLossMedicationHistory(BaseModel):
    glp1_medications: Optional[GLP1Medications] = Field(None, alias="glp1Medications", description="AI Agent: Collect information about GLP-1 medication history (Optional)")
    other_weight_loss_medications: Optional[List[str]] = Field(None, alias="otherWeightLossMedications", description="AI Agent: Ask 'Have you tried any other weight loss medications?' Examples: ['Phentermine', 'Orlistat', 'Contrave'] (Optional)")


class BariatricSurgeryHistory(BaseModel):
    has_bariatric_surgery_history: Optional[bool] = Field(None, alias="hasBariatricSurgeryHistory", description="AI Agent: Ask 'Have you had bariatric (weight loss) surgery?' Yes/No question")
    surgery_year: Optional[int] = Field(None, alias="surgeryYear", description="AI Agent: Ask 'What year did you have the surgery?'")
    surgery_type: Optional[List[str]] = Field(None, alias="surgeryType", description="AI Agent: Ask 'What type of bariatric surgery did you have?' Examples: ['Gastric bypass', 'Sleeve gastrectomy', 'Lap band'] (Optional)")
    pre_surgery_weight: Optional[float] = Field(None, alias="preSurgeryWeight", description="AI Agent: Ask 'What was your weight before surgery?'")
    lowest_weight_after_surgery: Optional[float] = Field(None, alias="lowestWeightAfterSurgery", description="AI Agent: Ask 'What was the lowest weight you reached after surgery?'")


class TreatmentPreferences(BaseModel):
    treatment_approach: Optional[TreatmentApproachEnum] = Field(None, alias="treatmentApproach", description="AI Agent: Ask 'What type of weight loss treatment are you most interested in?' Options: Surgical, Non-surgical, Both, Undecided")


class IntakeWeightHistory(BaseModel):
    current_vitals: CurrentVitals = Field(..., alias="currentVitals", description="AI Agent: Collect current height and weight measurements")
    weight_history: Optional[WeightHistory] = Field(None, alias="weightHistory", description="AI Agent: Collect historical weight information (Optional)")
    diet_history: Optional[DietHistory] = Field(None, alias="dietHistory", description="AI Agent: Collect information about past dieting attempts and eating patterns (Optional)")
    exercise_information: Optional[str] = Field(None, alias="exerciseInformation", description="AI Agent: Ask 'Tell me about your current exercise routine.'")
    weight_loss_medication_history: Optional[WeightLossMedicationHistory] = Field(None, alias="weightLossMedicationHistory", description="AI Agent: Collect information about previous weight loss medication use (Optional)")
    bariatric_surgery_history: Optional[BariatricSurgeryHistory] = Field(None, alias="bariatricSurgeryHistory", description="AI Agent: Collect information about previous bariatric surgery (Optional)")
    treatment_preferences: Optional[TreatmentPreferences] = Field(None, alias="treatmentPreferences", description="AI Agent: Collect patient preferences for treatment approach (Optional)")
    is_complete: bool = Field(default=False, alias="isComplete", description="System field: Indicates if this weight history section has been completed. Default: False")


# Medical History Models
class Medication(BaseModel):
    medication_name: Optional[str] = Field(None, alias="medicationName", description="AI Agent: Ask 'What is the name of this medication?'")
    strength: Optional[str] = Field(None, description="AI Agent: Ask 'What is the strength or dosage?'")
    directions: Optional[str] = Field(None, description="AI Agent: Ask 'How do you take this medication?'")


class Allergy(BaseModel):
    allergen: Optional[str] = Field(None, description="AI Agent: Ask 'What are you allergic to?'")
    reaction: Optional[str] = Field(None, description="AI Agent: Ask 'What reaction do you have?'")
    severity: Optional[SeverityEnum] = Field(None, description="AI Agent: Ask 'How severe is this allergy?' Options: Mild, Moderate, Severe (Optional)")


class FamilyHistoryItem(BaseModel):
    family_member: str = Field(..., alias="familyMember", description="AI Agent: Ask 'Which family member?'")
    medical_problem: str = Field(..., alias="medicalProblem", description="AI Agent: Ask 'What medical condition did they have?'")


class PastSurgery(BaseModel):
    surgery_type: str = Field(..., alias="surgeryType", description="AI Agent: Ask 'What type of surgery did you have?'")
    year: int = Field(..., description="AI Agent: Ask 'What year was the surgery?'")


class GERDHeartburn(BaseModel):
    has_gerd: Optional[bool] = Field(None, alias="hasGerd", description="AI Agent: Ask 'Do you have GERD or frequent heartburn?' Yes/No question")
    gerd_details: Optional[str] = Field(None, alias="gerdDetails", description="AI Agent: Ask 'Tell me about your GERD symptoms.'")


class Pancreatitis(BaseModel):
    has_pancreatitis: Optional[bool] = Field(None, alias="hasPancreatitis", description="AI Agent: Ask 'Have you ever had pancreatitis?' Yes/No question")
    number_of_attacks: Optional[int] = Field(None, alias="numberOfAttacks", description="AI Agent: Ask 'How many episodes of pancreatitis have you had?'")
    cause: Optional[str] = Field(None, description="AI Agent: Ask 'What caused your pancreatitis?'")


class SpecificConditions(BaseModel):
    gerd_heartburn: Optional[GERDHeartburn] = Field(None, alias="gerdHeartburn", description="AI Agent: Collect information about GERD/heartburn history (Optional)")
    pancreatitis: Optional[Pancreatitis] = Field(None, description="AI Agent: Collect information about pancreatitis history (Optional)")


class SocialHistory(BaseModel):
    smoking_summary: str = Field(..., alias="smokingSummary", description="AI Agent: Ask 'Tell me about your smoking history.'")
    alcohol_summary: str = Field(..., alias="alcoholSummary", description="AI Agent: Ask 'Tell me about your alcohol use.'")
    marijuana_summary: Optional[str] = Field(None, alias="marijuanaSummary", description="AI Agent: Ask 'Do you use marijuana?'")
    drug_summary: str = Field(..., alias="drugSummary", description="AI Agent: Ask 'Have you used any recreational drugs?'")
    employment_status: Optional[EmploymentStatusEnum] = Field(None, alias="employmentStatus", description="AI Agent: Ask 'What is your current employment status?' Options: Employed, Full-Time Student, Part-Time Student, Unemployed, Retired (Optional)")
    financial_situation: Optional[str] = Field(None, alias="financialSituation", description="AI Agent: Ask 'How would you describe your financial situation?'")
    employment_details: Optional[str] = Field(None, alias="employmentDetails", description="AI Agent: Ask 'What is your job or occupation?'")
    education_background: Optional[str] = Field(None, alias="educationBackground", description="AI Agent: Ask 'What is your highest level of education?'")


class IntakeMedicalHistory(BaseModel):
    current_medications: Optional[List[Medication]] = Field(None, alias="currentMedications", description="AI Agent: Ask 'What medications are you currently taking? Feel free to list all of them at once.' Include prescription and over-the-counter medications (Optional)")
    allergies: Optional[List[Allergy]] = Field(None, description="AI Agent: Ask 'Do you have any allergies to medications, foods, or other substances?' (Optional)")
    pmhx: Optional[List[str]] = Field(None, alias="PMHx", description="AI Agent: Ask 'What medical cond itions have you been diagnosed with?' Examples: ['Hypertension', 'Diabetes Type 2', 'Asthma'] (Optional)")
    pmhx_obesity_comorbid: Optional[List[str]] = Field(None, alias="PMHxObesityComorbid", description="AI Agent: Ask 'Do you have any weight-related health conditions?' Examples: ['Sleep apnea', 'High cholesterol', 'Joint pain'] (Optional)")
    family_history: Optional[List[FamilyHistoryItem]] = Field(None, alias="familyHistory", description="AI Agent: Ask 'What medical conditions run in your family?' Collect family member and condition pairs (Optional)")
    past_surgical_history: Optional[List[PastSurgery]] = Field(None, alias="pastSurgicalHistory", description="AI Agent: Ask 'Have you had any surgeries?' Collect surgery type and year (Optional)")
    specific_conditions: Optional[SpecificConditions] = Field(None, alias="specificConditions", description="AI Agent: Ask about specific conditions like GERD and pancreatitis (Optional)")
    social_history: SocialHistory = Field(..., alias="socialHistory", description="AI Agent: Collect social history including smoking, alcohol, drugs, employment, and education")
    is_complete: bool = Field(default=False, alias="isComplete", description="System field: Indicates if this medical history section has been completed. Default: False")


# Main Intake Session Model
class IntakeSession(BaseModel):
    """Complete intake session containing all four schema sections"""
    intake_demographics: Optional[IntakeDemographics] = Field(None, alias="intake_demographics", description="AI Agent: Collect patient demographic information including name, contact info, and address (Optional)")
    # intake_insurance: Optional[IntakeInsurance] = Field(None, alias="intake_insurance", description="AI Agent: Collect insurance information including primary and secondary coverage (Optional)")
    intake_weight_history: Optional[IntakeWeightHistory] = Field(None, alias="intake_weight_history", description="AI Agent: Collect weight management history including current vitals, diet history, and treatment preferences (Optional)")
    intake_medical_history: Optional[IntakeMedicalHistory] = Field(None, alias="intake_medical_history", description="AI Agent: Collect medical history including medications, allergies, past conditions, and social history (Optional)")
    completed: bool = Field(False, description="System field: Indicates if the intake session has been completed. Default: False")
    session_id: Optional[str] = Field(None, description="System field: Unique identifier for this intake session.")
    patient_mrn: Optional[str] = Field(None, description="System field: Patient's medical record number.")
    created_at: Optional[str] = Field(None, description="System field: Timestamp when session was created.")
    updated_at: Optional[str] = Field(None, description="System field: Timestamp when session was last updated.")
    rating: Optional[int] = Field(None, ge=1, le=5, description="AI Agent: Ask 'How would you rate your experience with this intake process?' Scale 1-5 (Optional)")
    comments: Optional[str] = Field(None, description="AI Agent: Ask 'Do you have any additional comments or concerns?'")