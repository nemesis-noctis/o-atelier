def calculate_character_price(commission_data):
    def calculate_base_price():  # Base prices
        prices_character_type = {
            "human": 80,
            "furry": 110,
            "chibi": 20,
            "simple_creature": 40,
            "complex_creature": 80
        }
        prices_clothing = {
            "mannequin": 0,
            "simple": 30,
            "complex": 60,
            "accessories": 90
        }
        prices_background = {
            "preset": 0,
            "simple": 20,
            "complex": 60
        }
        character_type_price = prices_character_type[commission_data["character_type"]]
        background_price = prices_background[commission_data["background"]]
        clothing_price = prices_clothing[commission_data["clothing"]]

        if commission_data["count"] > 1:
            character_type_price += (commission_data["count"] - 1) * character_type_price * 0.8
            clothing_price += (commission_data["count"] - 1) * clothing_price * 0.8


        elif commission_data["count"] > 4:
            character_type_price += (commission_data["count"] - 1) * character_type_price * 0.9
            clothing_price += (commission_data["count"] - 1) * clothing_price * 0.9

        if commission_data["character_type"] == "chibi":
            clothing_price /= 2
            background_price /= 2

        price = character_type_price + clothing_price + background_price

        return price + 20 if commission_data["fx"] == True else price + 0

    def calculate_discount_price(base_price):
        # Subtract prices
        prices_percent_body_type = {
            "bust": 0.6,
            "waist": 0.3,
            "full": 0
        }
        prices_percent_final_stage = {
            "sketch": 0.6,
            "lineart": 0.4,
            "flat_colour": 0.2,
            "render": 0
        }

        body_type_price = base_price - base_price * prices_percent_body_type[commission_data["body_type"]]

        if commission_data["character_type"] == "chibi" and commission_data["body_type"] == "bust":
            body_type_price *= 1.5
        elif commission_data["character_type"] == "chibi" and commission_data["body_type"] == "waist":
            body_type_price *= 1.2

        final_stage_price = body_type_price - body_type_price * prices_percent_final_stage[
            commission_data["final_stage"]]
        return final_stage_price

    def calculate_final_price(discount_price):
        prices_percent_art_type = {
            "illustration": 0,
            "scene": 0.4,
            "sheet": 0.5
        }
        prices_percent_aspect_ratio = {
            "1:1": 0,
            "3:2": 0.1,
            "16:9": 0.2,
            "1.85:1": 0.4
        }
        art_type_price = discount_price + discount_price * prices_percent_art_type[commission_data["art_type"]]
        aspect_ratio_price = art_type_price + art_type_price * prices_percent_aspect_ratio[
            commission_data["aspect_ratio"]]
        return aspect_ratio_price

    base_price = calculate_base_price()
    discount_price = calculate_discount_price(base_price)
    final_price = calculate_final_price(discount_price)
    if final_price < 15:
        final_price = 15

    return final_price


def calculate_landscape_price(self, commission_data):
    prices_complexity = {
        "simple": 60,
        "complex": 90
    }


def calculate_object_price(self, commission_data):
    prices_complexity = {
        "simple": 30,
        "complex": 60
    }
    prices_background = {
        "preset": 0,
        "simple": 10,
        "complex": 30
    }
