def calculate_character_price(commission_data):
    def calculate_base_price():  # Base prices
        prices_character_type = {
            "human": 50,
            "furry": 60,
            "chibi": 20,
            "simple_creature": 30,
            "complex_creature": 60
        }
        prices_clothing = {
            "mannequin": 0,
            "simple": 10,
            "complex": 30,
            "accessories": 40
        }
        prices_background = {
            "preset": 0,
            "simple": 10,
            "complex": 30
        }
        character_type_price = prices_character_type[commission_data["character_type"]]
        background_price = prices_background[commission_data["background"]]
        clothing_price = prices_clothing[commission_data["clothing"]]

        if commission_data["count"] <= 2:
            character_type_price += (commission_data["count"] - 1) * character_type_price * 0.65
            clothing_price += (commission_data["count"] - 1) * clothing_price * 0.65

        elif commission_data["count"] > 2:
            character_type_price += (commission_data["count"] - 1) * character_type_price * 0.8
            clothing_price += (commission_data["count"] - 1) * clothing_price * 0.8

        if commission_data["character_type"] == "chibi":
            clothing_price /= 2
            background_price /= 2

        base_price = character_type_price + clothing_price + background_price

        return base_price + 10 if commission_data["fx"] == True else base_price

    def calculate_discount_price(base_price):
        # Subtract prices
        prices_percent_body_type = {
            "bust": 0.6,
            "waist": 0.3,
            "full": 0
        }
        prices_percent_final_stage = {
            "lineart": 0.4,
            "flat_colour": 0.2,
            "render": 0
        }

        body_type_price = base_price - base_price * prices_percent_body_type[commission_data["body_type"]]

        if commission_data["character_type"] == "chibi" and commission_data["body_type"] == "bust":
            body_type_price *= 1.5
        elif commission_data["character_type"] == "chibi" and commission_data["body_type"] == "waist":
            body_type_price *= 1.2

        return body_type_price - body_type_price * prices_percent_final_stage[commission_data["final_stage"]]

    def calculate_final_price(discount_price):
        prices_percent_art_type = {
            "illustration": 0,
            "scene": 0.2,
            "sheet": 2
        }
        prices_percent_aspect_ratio = {
            "1:1": 0,
            "3:2": 0.1,
            "16:9": 0.2,
            "1.85:1": 0.3
        }
        art_type_price = discount_price + discount_price * prices_percent_art_type[commission_data["art_type"]]
        return art_type_price + art_type_price * prices_percent_aspect_ratio[commission_data["aspect_ratio"]]

    base_price = calculate_base_price()
    discount_price = calculate_discount_price(base_price)
    final_price = calculate_final_price(discount_price)
    if final_price < 15:
        final_price = 15

    return {"brl": round(final_price, 2), "usd": round(final_price - final_price * 0.6, 2)}


########################################################################################################################
def calculate_landscape_price(commission_data):
    def calculate_base_price():
        prices_complexity = {
            "simple": 30,
            "complex": 70
        }

        base_price = prices_complexity[commission_data["complexity"]]
        return base_price + 10 if commission_data["fx"] == True else base_price

    def calculate_discount_price(base_price):
        # Subtract prices
        prices_percent_final_stage = {
            "lineart": 0.3,
            "flat_colour": 0.2,
            "render": 0
        }

        return base_price - base_price * prices_percent_final_stage[commission_data["final_stage"]]

    def calculate_final_price(discount_price):
        prices_percent_aspect_ratio = {
            "1:1": 0,
            "3:2": 0.4,
            "16:9": 0.7,
            "1.85:1": 1
        }

        return discount_price + discount_price * prices_percent_aspect_ratio[commission_data["aspect_ratio"]]

    base_price = calculate_base_price()
    discount_price = calculate_discount_price(base_price)
    final_price = calculate_final_price(discount_price)
    if final_price < 15:
        final_price = 15

    return {"brl": round(final_price, 2), "usd": round(final_price - final_price * 0.6, 2)}


########################################################################################################################
def calculate_object_price(commission_data):
    def calculate_base_price():
        prices_complexity = {
            "simple": 15,
            "complex": 30
        }
        prices_background = {
            "preset": 0,
            "simple": 10,
            "complex": 25
        }

        complexity_price = prices_complexity[commission_data["complexity"]]
        background_price = prices_background[commission_data["background"]]

        if commission_data["count"] > 1:
            complexity_price += (commission_data["count"] - 1) * complexity_price * 0.8

        elif commission_data["count"] > 4:
            complexity_price += (commission_data["count"] - 1) * complexity_price * 0.9

        base_price = complexity_price + background_price

        return base_price + 10 if commission_data["fx"] == True else base_price

    def calculate_discount_price(base_price):
        # Subtract prices
        prices_percent_final_stage = {
            "lineart": 0.3,
            "flat_colour": 0.2,
            "render": 0
        }

        return base_price - base_price * prices_percent_final_stage[commission_data["final_stage"]]

    def calculate_final_price(discount_price):
        prices_percent_aspect_ratio = {
            "1:1": 0,
            "3:2": 0.2,
            "16:9": 0.4,
            "1.85:1": 0.6
        }
        prices_percent_art_type = {
            "illustration": 0,
            "scene": 0.2,
            "sheet": 2
        }

        aspect_ratio_price = discount_price + discount_price * prices_percent_aspect_ratio[
            commission_data["aspect_ratio"]]
        return aspect_ratio_price + aspect_ratio_price * prices_percent_art_type[commission_data["art_type"]]

    base_price = calculate_base_price()
    discount_price = calculate_discount_price(base_price)
    final_price = calculate_final_price(discount_price)
    if final_price < 15:
        final_price = 15
        
    return {"brl": round(final_price, 2), "usd": round(final_price - final_price * 0.6, 2)}
