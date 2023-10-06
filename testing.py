# automated testing file
# get all the fights from a certain date from ufc events website
# 

import requests
from bs4 import BeautifulSoup
import csv
import process_fights_elo
from datetime import datetime
import ml_training_duplication
import predict_fights_elo


# TODO: figure out how to do rematches (maybe just use a set)
def ml_elo(p1, p2):
    input_txt_filename = "ml_elo.txt"
    id = -1
    flag = False
    prob_win = 0

    with open(input_txt_filename, mode="r") as input_file:
        lines = input_file.readlines()
        for line in lines:
            if ("fighter_names" in line):
                flag = True
            elif ("dtype:" in line):
                flag = False
            # fields = line.strip().split(' ')
            # fields = list(filter(lambda a: a != '', fields))
            fields = line.strip().split('*')
            # print(fields)

            if (flag):
                if (fields[0] != "fighter_names" and len(fields) > 1):
                    fighter_name = fields[0][3:].strip()
                    opponent_name = fields[1].strip()
                    # print(fighter_name + " " + opponent_name)
                    if (p1 == fighter_name and p2 == opponent_name):
                        id = fields[0][0:3].strip()
                        print(id)
            if (len(fields) > 0 and "probability_win" in line):
                    flag = True
            elif (id != -1 and flag and fields[0][0:3].strip() == id):
                # print(fields[0] + " " + fields[1] + " " + id)
                fields = line.strip().split(' ')
                fields = list(filter(lambda a: a != '', fields))
                prob_win = fields[-1]

    if id == -1:
        # test.write(f"Fighter {p1} has less than 5 fights.\n")
        return
    return prob_win

bankroll = 1000.00

def kelly_criterion(odds, prob_win):
        kc = 0
        if (odds < 0):
            n = 100 / -odds
            kc = (n * prob_win - (1 - prob_win)) / n
        else:
            n = odds / 100  
            kc = (n * prob_win - (1 - prob_win)) / n
        return kc

def odds_to_prob(odds):
    if odds >= 0:
        prob = 100 / (odds + 100)
    else:
        prob = -odds / (-odds + 100)
    
    return prob

with open("testing.txt", "w") as test:

    urls = []
    urls.append("https://www.ufc.com/events")
    # end of page 5 is 1 year ago, usman vs edwards
    for i in range(1, 2):
        urls.append("https://www.ufc.com/events?page=" + str(i))    
    all_fight_card_links = []
    for url in urls:
        # Send a GET request to the events page
        response = requests.get(url)


        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all the fight card links
            fight_card_links = []

            # Extract the links to individual fight card pages
            for card_div in soup.find_all("div", {"class": "c-card-event--result__logo"}):
                card_link = card_div.find("a")
                if card_link:
                    fight_card_links.append("https://www.ufc.com" + card_link.get("href"))
            

            for link in fight_card_links:
                all_fight_card_links.append(link)
                

    all_fight_card_links.reverse()
    # for links in all_fight_card_links:
    #     print(links)
        # Loop through each fight card link and scrape the odds
    
    cnt = 0
    # UPDATE FIGHTER STATS TO THE DATE OF THE STARTING TEST
    process_fights_elo.event_to_drop = "2023-06-10"
    process_fights_elo.main()

    # UPDATE PREDICT_FIGHTS_ELO.CSV WITH NEW FIGHTER STATS
    predict_fights_elo.main()
    for fight_card_link in all_fight_card_links:
        print(fight_card_link)
        response = requests.get(fight_card_link)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find and extract the odds as shown in your original HTML
            odds_wrappers = soup.find_all(class_='c-listing-fight__odds-wrapper')

            fighter_name_divs = soup.find_all("div", {"class": "c-listing-fight__corner-name"})
            fighter_names = []

            for name_div in fighter_name_divs:
                given_name_element = name_div.find("span", {"class": "c-listing-fight__corner-given-name"})
                family_name_element = name_div.find("span", {"class": "c-listing-fight__corner-family-name"})
                if given_name_element and family_name_element:
                    given_name = given_name_element.text.strip()
                    family_name = family_name_element.text.strip()
                    fighter_names.append(f"{given_name} {family_name}")
                else:
                    fighter_name_link = name_div.find("a")
                    if fighter_name_link:
                        fighter_name = fighter_name_link.text.strip()
                        fighter_names.append(fighter_name)
                    else:
                        fighter_names.append("Fighter Name Not Found")

            # Find all elements with the class "c-listing-fight__corner-body--blue"
            blue_corner_elements = soup.find_all(class_='c-listing-fight__corner-body--blue')
            winners = []
            
            for blue_corner in blue_corner_elements:
                if blue_corner.find(class_='c-listing-fight__outcome--Win'):
                    winners.append("win")
                elif blue_corner.find(class_='c-listing-fight__outcome--Loss'):
                    winners.append("loss")
                else:
                    winners.append("draw/no contest")
            
            if (len(winners) == 0):
                continue
            
            test.write(f"Bankroll: ${bankroll:.2f}\n")
            test.write(f"Fight Card: {fight_card_link}\n")
            test.write("---\n")

            # Extract and print the odds for each fight on the current card
            for i in range(0, len(fighter_names), 2):
                fighter1_name = fighter_names[i]
                fighter2_name = fighter_names[i + 1]
                winner = winners[i // 2]
                winner_name = ""
                if winner == "win":
                    winner_name = fighter2_name
                elif winner == "loss":
                    winner_name = fighter1_name
                else:
                    winner_name = "draw/no contest"

                odds_wrapper = odds_wrappers[i // 2]
                odds_elements = odds_wrapper.find_all(class_='c-listing-fight__odds-amount')
                odds_values = [element.get_text() for element in odds_elements]

                if len(odds_values) == 2:
                    fighter1_odds = odds_values[0]
                    fighter1_odds = fighter1_odds.replace('−', '-')  
                    fighter2_odds = odds_values[1]
                    fighter2_odds = fighter2_odds.replace('−', '-')  
                    if (ml_elo(fighter1_name, fighter2_name) == None or ml_elo(fighter2_name, fighter1_name) == None):
                        # test.write("Fighter not found in the text file.\n")
                        test.write("---\n")
                        continue
                    avb_win = float(ml_elo(fighter1_name, fighter2_name)) #70
                    avb_lose = 1 - avb_win
                    bva_win = float(ml_elo(fighter2_name, fighter1_name))
                    bva_lose = 1 - bva_win #60
                    odds1_prob = 0
                    odds2_prob = 0
                    if (fighter1_odds != "-" and fighter2_odds != "-"):
                        odds1_prob = odds_to_prob(int(fighter1_odds))
                        odds2_prob = odds_to_prob(int(fighter2_odds))
                    a_win_avg=avb_win
                    b_win_avg=bva_win
                    if(abs(avb_win-odds1_prob) > abs(bva_lose-odds1_prob)):
                        a_win_avg=bva_lose
                    if(abs(bva_win-odds2_prob) > abs(avb_lose-odds2_prob)):
                        b_win_avg=avb_lose
                    # a_win_avg = (float(avb_win) + float(bva_lose)) / 2
                    # b_win_avg = (float(bva_win) + float(avb_lose)) / 2
                    kc_a = 0
                    kc_b = 0
                    if (fighter1_odds != "-" and fighter2_odds != "-"):
                        kc_a = kelly_criterion(int(fighter1_odds), a_win_avg)
                        kc_b = kelly_criterion(int(fighter2_odds), b_win_avg)
                    test.write(f"{fighter1_name}: {fighter1_odds} {a_win_avg:.2f} {kc_a:.2f}\n")
                    test.write(f"{fighter2_name}: {fighter2_odds} {b_win_avg:.2f} {kc_b:.2f}\n")
                    if a_win_avg > b_win_avg:
                        test.write(f"{fighter1_name} ")
                        if (kc_a > 0):
                            bet = bankroll * (0.1) * kc_a
                            potential_return = 0
                            odds = int(fighter1_odds)
                            if (odds < 0):
                                potential_return = bet * (100 / -odds)
                            else:
                                potential_return = bet * (odds / 100)
                            test.write(f"${bet:.2f} (bet) pt: ${bet + potential_return:.2f} +${potential_return:.2f}")
                            if (winner_name == fighter1_name):
                                test.write(" (win)")
                                bankroll += potential_return
                            else:
                                test.write(" (loss)")
                                bankroll -= bet
                        else:
                            test.write(f"(no bet)")
                        test.write("\n")
                    else:
                        test.write(f"{fighter2_name} ")
                        if (kc_b > 0):
                            bet = bankroll * (0.1) * kc_b
                            potential_return = 0
                            odds = int(fighter2_odds)
                            if (odds < 0):
                                potential_return = bet * (100 / -odds)
                            else:
                                potential_return = bet * (odds / 100)
                            test.write(f"${bet:.2f} (bet) pt: ${bet + potential_return:.2f} +${potential_return:.2f}")
                            if (winner_name == fighter2_name):
                                test.write(" (win)")
                                bankroll += potential_return
                            else:
                                test.write(" (loss)")
                                bankroll -= bet
                        else:
                            test.write(f"(no bet)")
                        test.write("\n")
                        

                    test.write("---\n")
        
            if cnt % 10 == 0:
                #  UPDATE FIGHTER STATS AFTER EACH EVENT
                meta_tag = soup.find('meta', attrs={'property': 'og:description'})
                content = meta_tag.get('content')
                date_str = content.split('On ')[-1]  
                date_str = date_str.split('on ')[-1]
                date_str = date_str.split('.')[0]
                date_obj = ""
                formatted_date = ""
                date_formats = ['%A, %B %d, %Y', '%B %d, %Y', '%A %B %d, %Y']
                for date_format in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, date_format)
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                        print("date obj: ", date_obj)
                        break  # Break out of the loop if parsing succeeds
                    except ValueError:
                        pass  # Continue to the next format if parsing fails
                if (formatted_date == ""):
                    print(date_str)
                process_fights_elo.event_to_drop = date_obj
                process_fights_elo.main()

                # UPDATE PREDICT_FIGHTS_ELO.CSV WITH NEW FIGHTER STATS
                predict_fights_elo.main()

                #  UPDATE TRAINING AND GET NEW PREDICTIONS
                # formatted_date = date_obj.strftime('%Y-%m-%d')
                print(formatted_date)
                ml_training_duplication.date_to_train = formatted_date
                ml_training_duplication.main()

                
            # most recent fight
            if (fight_card_link == "https://www.ufc.com/event/ufc-fight-night-september-23-2023"):
                break
            cnt += 1

        else:
            test.write(f"Failed to retrieve the fight card page. Status code: {response.status_code}\n")
    else:
        test.write(f"Failed to retrieve the events page. Status code: {response.status_code}\n")
    test.write(f"Bankroll: ${bankroll:.2f}\n")