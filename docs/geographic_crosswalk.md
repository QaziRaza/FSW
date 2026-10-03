# Geographic crosswalk rules

The surveillance outcome is city-based; PSLM predictors are district estimates with separate urban strata. Every match is therefore explicit and auditable rather than a fuzzy string join.

Large-city PSLM strata support `close` matches for Lahore, Gujranwala, Faisalabad, Rawalpindi, Multan, Sargodha, Karachi, Hyderabad, Sukkur, Peshawar, and Quetta. Karachi is nevertheless graded `composite` because the surveillance city/metropolitan geography does not map cleanly to one stable district unit. Nawabshah is matched to Shaheed Benazirabad in 2014–15 and is marked `close` with a rename note. Other city-to-district urban matches are `district_proxy`.

The machine-readable crosswalk is generated at `data/processed/geographic_crosswalk.csv` and includes round, source city spelling, canonical city ID, economic geography, match grade, and notes.

