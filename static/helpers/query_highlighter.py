from unidecode import unidecode


def remove_punctuation(str):
  result = ''.join(filter(lambda x: x.isalpha() or x.isdigit() or x.isspace(), str))
  return result

# Highlight tekst crtl F style
# NOTE: file op true gaat over list view
def highlight_sentence(query, file_sentence, file=True):
    # kijk of een match met de query is in de tekst
    simplified_file_sentence = remove_punctuation(unidecode(file_sentence["content"]).lower()).split(" ")
    query_length = len(query.split(" "))
    from_to_dict = {}
    for idx, word in enumerate(simplified_file_sentence):
        end = idx + query_length
        
        # fitler lege selections
        selections = simplified_file_sentence[idx:end]
        if len(selections) == query_length and selections[-1] != "":
            
            length_match = 0
            for selection, query_list in zip(selections, query.lower().split(" ")):
                
                if selection == query_list:
                    length_match += 1

                    # query gevonden in tekst
                    if length_match == query_length:
                        from_to_dict[idx] = end

    # maak een nieuwe zin met highlights er in
    highlighted_sentence = ""
    new_sentence = file_sentence["content"].split(" ")
    reserved = -1
    sentence_highlighted_words = 0
    for x in range(len(new_sentence)):

        if x in from_to_dict.keys():
            sentence_highlighted_words += 1

            x_end = from_to_dict[x]
            
            reserved = x_end

            # 1 woord lange query
            if x == x_end:
                highlighted_sentence += f"<span class='{'highlight' if file else 'highlight-list'}'>{new_sentence[x]}</span> "
            # langere query
            else:
                highlighted_sentence += f"<span class='{'highlight' if file else 'highlight-list'}'>{' '.join(str(w) for w in new_sentence[x:x_end])}</span> "

        elif not x <= reserved:
            highlighted_sentence += f"{new_sentence[x]} "

    # word count alleen sturen voor files
    if file:
        return highlighted_sentence, sentence_highlighted_words
    
    else:
        return highlighted_sentence