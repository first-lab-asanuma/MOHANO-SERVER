from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.errors import ServiceError
from app.core.security import utc_now
from app.db.session import SessionLocal
from app.models.profile import Profile, ProfileInterest, ProfileLanguage, ProfilePhotoRecord
from app.models.user import User
from app.schemas.profile import ProfilePhoto, ProfilePhotoCreateRequest, ProfileResponse, ProfileUpdateRequest, PublicProfile


class ProfileRepository:
    def get(self, user_id: str) -> ProfileResponse:
        with SessionLocal.begin() as db:
            return self._response(self._profile(db, user_id))

    def update(self, user_id: str, payload: ProfileUpdateRequest) -> ProfileResponse:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            values = payload.model_dump(exclude_unset=True)
            for name in ('nickname', 'nationality', 'gender', 'birth_date', 'age_visible', 'timezone', 'mbti', 'introduction'):
                if name in values:
                    setattr(profile, name, values[name])
            if 'languages' in values:
                profile.languages[:] = [ProfileLanguage(language_code=value) for value in values['languages'] or []]
            if 'interest_codes' in values:
                profile.interests[:] = [ProfileInterest(interest_code=value) for value in values['interest_codes'] or []]
            profile.onboarding_completed = bool(profile.nationality and profile.gender and profile.birth_date)
            db.flush()
            return self._response(profile)

    def add_photo(self, user_id: str, payload: ProfilePhotoCreateRequest) -> ProfileResponse:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            if len(profile.photos) >= 5:
                raise ServiceError('photo_limit_reached', 'A profile can have up to five photos', 400)
            if payload.is_primary:
                for photo in profile.photos:
                    photo.is_primary = False
            profile.photos.append(ProfilePhotoRecord(image_ref=payload.image_ref, position=len(profile.photos), is_primary=payload.is_primary or not profile.photos))
            db.flush()
            return self._response(profile)

    def add_photo_from_storage(self, user_id: str, photo_id: str, storage_key: str) -> ProfileResponse:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            if len(profile.photos) >= 5:
                raise ServiceError('photo_limit_reached', 'A profile can have up to five photos', 400)
            profile.photos.append(
                ProfilePhotoRecord(
                    id=photo_id,
                    image_ref=storage_key,
                    position=len(profile.photos),
                    is_primary=not profile.photos,
                ),
            )
            db.flush()
            return self._response(profile)

    def ensure_photo_capacity(self, user_id: str) -> None:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            if len(profile.photos) >= 5:
                raise ServiceError('photo_limit_reached', 'A profile can have up to five photos', 400)

    def photo_storage_key(self, user_id: str, photo_id: str) -> str:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            photo = next((item for item in profile.photos if item.id == photo_id), None)
            if photo is None:
                raise ServiceError('photo_not_found', 'Photo not found', 404)
            return photo.image_ref

    def remove_photo(self, user_id: str, photo_id: str) -> ProfileResponse:
        with SessionLocal.begin() as db:
            profile = self._profile(db, user_id)
            photo = next((item for item in profile.photos if item.id == photo_id), None)
            if photo is None:
                raise ServiceError('photo_not_found', 'Photo not found', 404)
            was_primary = photo.is_primary
            profile.photos.remove(photo)
            for index, item in enumerate(profile.photos):
                item.position = index
            if was_primary and profile.photos:
                profile.photos[0].is_primary = True
            db.flush()
            return self._response(profile)

    def public(self, user_id: str) -> PublicProfile:
        with SessionLocal.begin() as db:
            return self._public(self._profile(db, user_id))

    def seed_candidates(self) -> None:
        records = [
            ('mock-sakura', 'Sakura', 'JP', 'woman', date(2000, 7, 18), ['ja', 'en'], 'ENFP', ['coffee_walks', 'photography', 'music'], 'I like small cafés, taking photos, and conversations that make an ordinary day feel lighter.'),
            ('mock-hana', 'Hana', 'JP', 'woman', date(2000, 4, 12), ['ja', 'en'], 'INFP', ['bookstores', 'photography', 'deep_talks'], 'A quiet walk and a good question can make an ordinary day memorable.'),
            ('mock-yuki', 'Yuki-Mock', 'JP', 'man', date(1998, 9, 4), ['ja', 'ko'], 'ISFJ', ['coffee_walks', 'indie_films', 'languages'], 'Looking for someone to talk with slowly after a long day.'),
            ('mock-mina', 'Mina', 'KR', 'woman', date(1999, 1, 22), ['ko', 'en'], 'ENFJ', ['coffee_walks', 'music', 'travel'], 'Small everyday stories are my favorite conversation starters.'),
        ]
        countries = ('JP', 'KR', 'US', 'CA', 'GB', 'AU', 'DE', 'FR', 'SG', 'TW')
        names = (
            'Aoi', 'Ren', 'Mio', 'Kai', 'Yuna', 'Haru', 'Sora', 'Jin',
            'Nari', 'Min', 'Emma', 'Noah', 'Lina', 'Theo', 'Sena', 'Riku',
        )
        mbti_types = ('ENFP', 'INFP', 'ISFJ', 'ENTJ', 'INFJ', 'ESFP', 'INTP', 'ENFJ')
        interest_sets = (
            ['coffee_walks', 'photography', 'music'],
            ['bookstores', 'indie_films', 'deep_talks'],
            ['languages', 'travel', 'music'],
            ['photography', 'travel', 'coffee_walks'],
        )
        language_sets = (['ja', 'en'], ['ko', 'en'], ['en'], ['ja', 'ko'], ['en', 'fr'])
        introductions = (
            'I enjoy slow conversations and finding small places worth remembering.',
            'A good playlist, a walk, and an honest question can make my day.',
            'I would love to share everyday stories across languages and cultures.',
            'Looking for a kind conversation that starts naturally and stays curious.',
        )
        for index in range(1, 97):
            records.append(
                (
                    f'seed-demo-{index:03d}',
                    f'{names[(index - 1) % len(names)]} {index:02d}',
                    countries[(index - 1) % len(countries)],
                    ('woman', 'man', 'non_binary')[(index - 1) % 3],
                    date(1988 + (index % 18), (index % 12) + 1, (index % 28) + 1),
                    language_sets[(index - 1) % len(language_sets)],
                    mbti_types[(index - 1) % len(mbti_types)],
                    interest_sets[(index - 1) % len(interest_sets)],
                    introductions[(index - 1) % len(introductions)],
                )
            )
        with SessionLocal.begin() as db:
            for user_id, *_ in records:
                user = db.get(User, user_id)
                if user is None:
                    db.add(
                        User(
                            id=user_id,
                            status='seed',
                            last_active_at=utc_now(),
                            call_notifications_enabled=True,
                            push_token=f'local-seed-token-{user_id}',
                        )
                    )
                elif user.status == 'seed':
                    user.call_notifications_enabled = True
                    user.push_token = f'local-seed-token-{user_id}'
            # Profile.user_id의 FK 대상인 seed user를 먼저 DB에 반영한다.
            db.flush()
            for user_id, nickname, country, gender, birthday, languages, mbti, interests, intro in records:
                if db.get(Profile, user_id) is None:
                    db.add(Profile(user_id=user_id, nickname=nickname, nationality=country, gender=gender, birth_date=birthday, languages=[ProfileLanguage(language_code=value) for value in languages], interests=[ProfileInterest(interest_code=value) for value in interests], mbti=mbti, introduction=intro, onboarding_completed=True))

    def _profile(self, db, user_id: str) -> Profile:
        if db.get(User, user_id) is None:
            raise ServiceError('user_unavailable', 'User unavailable', 401)
        profile = db.scalar(select(Profile).options(selectinload(Profile.languages), selectinload(Profile.interests), selectinload(Profile.photos)).where(Profile.user_id == user_id))
        if profile is None:
            profile = Profile(user_id=user_id)
            db.add(profile)
            db.flush()
        return profile

    def _response(self, profile: Profile) -> ProfileResponse:
        public = self._public(profile)
        return ProfileResponse(
            user_id=profile.user_id,
            **public.model_dump(exclude={'age'}),
            age=self._age(profile.birth_date),
            birth_date=profile.birth_date,
            timezone=profile.timezone,
            photos=self._photos(profile),
            onboarding_completed=profile.onboarding_completed,
        )

    def _public(self, profile: Profile) -> PublicProfile:
        age = self._age(profile.birth_date)
        photos = self._photos(profile)
        return PublicProfile(nickname=profile.nickname, nationality=profile.nationality, gender=profile.gender, age=age if profile.age_visible else None, age_visible=profile.age_visible, languages=[item.language_code for item in profile.languages], mbti=profile.mbti, interest_codes=[item.interest_code for item in profile.interests], introduction=profile.introduction, primary_photo=next((item for item in photos if item.is_primary), None))

    @staticmethod
    def _age(birth_date: date | None) -> int | None:
        if birth_date is None:
            return None
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def _photos(profile: Profile) -> list[ProfilePhoto]:
        return [ProfilePhoto(photo_id=item.id, image_url=item.image_ref, position=item.position, is_primary=item.is_primary) for item in profile.photos]
