from app.schemas.user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenData
)
from app.schemas.company import (
    CompanyBase, CompanyCreate, CompanyUpdate, CompanyResponse
)
from app.schemas.property import (
    PropertyBase, PropertyCreate, PropertyUpdate, PropertyResponse,
    BuildingBase, BuildingCreate, BuildingUpdate, BuildingResponse,
    PremiseBase, PremiseCreate, PremiseUpdate, PremiseResponse, PremiseListResponse
)
from app.schemas.tenant import (
    TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantDetailResponse,
    TenantContactBase, TenantContactCreate, TenantContactUpdate, TenantContactResponse
)
from app.schemas.contract import (
    ContractBase, ContractCreate, ContractUpdate, ContractResponse, ContractDetailResponse,
    PaymentScheduleBase, PaymentScheduleCreate, PaymentScheduleUpdate, PaymentScheduleResponse
)
from app.schemas.payment import (
    PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse, PaymentDetailResponse,
    PaymentDocumentBase, PaymentDocumentCreate, PaymentDocumentResponse,
    PaymentApprovalRequest, PaymentUploadRequest
)
from app.schemas.lead import (
    LeadBase, LeadCreate, LeadUpdate, LeadResponse,
    LeadCommunicationCreate, LeadCommunicationResponse
)
from app.schemas.notification import (
    NotificationBase, NotificationCreate, NotificationResponse, NotificationMarkRead
)
from app.schemas.reports import (
    OccupancyReport, FinancialReport, PropertyFinancialReport,
    TenantPaymentReport, LeadConversionReport, LeadSourceReport,
    DashboardMetrics, PropertyMetrics
)
