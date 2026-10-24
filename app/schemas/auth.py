from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    needs_onboarding: bool = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class GoogleExchangeRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=8192)
    # Do not default to account creation: a stale client must not accidentally
    # create an account from the existing-account sign-in path.
    create_account: bool
