Classify each question into one SQL shape and return CSV id,question,predicted_sql in input order from `Week_03_Prompting/Assignments/Task_2/data/restaurants_dataset.csv` (column `question` only, never `result`), grounded in `restaurants-schema.csv` and `restaurants-db.txt`.

Output set: RESTAURANT always; +LOCATION if street asked; +GEOGRAPHIC if county/region asked; unclear inputs still get valid SQL returning empty. Preserve duplicates, no DISTINCT unless asked.

Follow this exact shape:
Q: Give me italian restaurants in palo alto with a rating above 3.
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON LOCATION.RESTAURANT_ID = RESTAURANT.ID WHERE LOWER(RESTAURANT.FOOD_TYPE) = LOWER('italian') AND LOWER(RESTAURANT.CITY_NAME) = LOWER('palo alto') AND RESTAURANT.RATING > 3;
Q: I still cannot decide soup or pie for breakfast, give me mexican restaurants in concord with a rating above 2.
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON LOCATION.RESTAURANT_ID = RESTAURANT.ID WHERE LOWER(RESTAURANT.FOOD_TYPE) = LOWER('mexican') AND LOWER(RESTAURANT.CITY_NAME) = LOWER('concord') AND RESTAURANT.RATING > 2;
Q: Give me a restaurant on timber creek dr in san jose with a rating above 1.7.
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON LOCATION.RESTAURANT_ID = RESTAURANT.ID WHERE LOWER(LOCATION.STREET_NAME) = LOWER('timber creek dr') AND LOWER(RESTAURANT.CITY_NAME) = LOWER('san jose') AND RESTAURANT.RATING > 1.7;
Q: Give me restaurants in the bay area with a rating above 2.
SQL: SELECT LOCATION.HOUSE_NUMBER, RESTAURANT.NAME FROM RESTAURANT JOIN LOCATION ON LOCATION.RESTAURANT_ID = RESTAURANT.ID JOIN GEOGRAPHIC ON GEOGRAPHIC.CITY_NAME = RESTAURANT.CITY_NAME WHERE LOWER(GEOGRAPHIC.REGION) = LOWER('bay area') AND RESTAURANT.RATING > 2;

Tie-break: request beats fluff; explicit street/city beats inferred region. Output only CSV rows to `Week_03_Prompting/Assignments/Task_2/predictions_fewshot.csv`, no explanations, no invented tables or columns.
