import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from lxml import html
from collections import Counter
from urllib.parse import urlparse
from collections import defaultdict

unique_pages = set()
longest_page_url = ""
longest_page_word_count = 0
subdomain_count = defaultdict(int)

word_frequencies = Counter()
seen_checksums = set()
seen_docs = []

# Stop words sourced from: https://www.ranks.nl/stopwords
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
    "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll",
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why",
    "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}


def scraper(url, resp):
    
    #ensure no duplicate links within a crawl
    #changed from starter code because avoid duplicate links from the same page and should skip bad pages and track unique pages
    links = extract_next_links(url, resp)

    result = []
    seen = set()

    for link in links:
        if not link:
            continue

        link = link.strip()

        if link in seen:
            continue

        if is_valid(link):
            seen.add(link)
            result.append(link)

    return result

#Used to ensure no HTML markup
def get_words_from_html(soup):
    text = soup.get_text(separator=" ")
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return words

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    #check file status 
    global longest_page_url, longest_page_word_count
    global word_frequencies

    hyperlinks = []
    if resp.status!=200:
        print(resp.error)
        return hyperlinks
    elif resp.raw_response==None or not resp.raw_response.content:
        return hyperlinks

    #add to unique pages and update report.txt
    defrag, _ = urldefrag(url)

     ## write subdomain code here
    if defrag not in unique_pages:
        unique_pages.add(defrag)
        parsed = urlparse(url)
        net_loc = parsed.netloc
        
        if net_loc.endswith("uci.edu"):
            if net_loc == "uci.edu":
                pass
            else:
                subdomain_count[net_loc] += 1

    ## duplicate check
    content = resp.raw_response.content
    if is_exact_duplicate(content) or is_near_duplicate(content):
        return hyperlinks

    #through trial and error, these were good values. Started 10 mil then went down from there
    if len(resp.raw_response.content) > 3_000_000: #for too big of a file
        print("File too large to parse")
        return hyperlinks
    elif len(resp.raw_response.content)<50: #for too small of files
        return hyperlinks

    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    words = get_words_from_html(soup)
    word_count = len(words)

    #longest page count code
    filtered_words = []

    for word in words:
        if word not in STOP_WORDS and len(word) > 1:
            filtered_words.append(word)

    word_frequencies.update(filtered_words)

    if word_count > longest_page_word_count:
        longest_page_word_count = word_count
        longest_page_url = defrag
   
    #generate report
    with open('report.txt', 'w') as f:
        pages = str(len(unique_pages))
        f.write(f"Final number of unique pages: {pages}\n\n")

        f.write("Longest page by word count:\n")
        f.write(f"URL: {longest_page_url}\n")
        f.write(f"Word count: {longest_page_word_count}\n")
        
        f.write("\n50 most common words:\n")
        for word, count in word_frequencies.most_common(50):
            f.write(f"{word}, {count}\n")

        f.write(f"\nTotal unique subdomains found: {len(subdomain_count)}\n")
        f.write("Subdomain counts ordered by subdomain alphabetically:\n")
        for key, value in sorted(subdomain_count.items(), key=lambda x: x[0]):
            f.write(f"{key}, {value}\n")
            
    #find all links on a page aka find all the anchor tags 
    #ValueError added to prevent from downloading "bad links"
    for link in soup.find_all('a', href=True):
        try:
            joined = urljoin(url, link['href'])
            joined, _ = urldefrag(joined)
            hyperlinks.append(joined)
        except ValueError:
            continue

    return hyperlinks

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    
    try:
       
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        domains = {
            'ics.uci.edu',
            'cs.uci.edu', 
            'informatics.uci.edu',
            'stat.uci.edu'
        }
        #running into an issue where we were crawling physics.uci.edu
        if not any(parsed.netloc.endswith("."+i) for i in domains):
            return False
        
        ## strip off fragment
        parsed = parsed._replace(fragment = "")
        
        ## invalid keywords for trap checks
        bad_words = {"signup", "logout", "login", "register", "calendar", "events", "event", "events_calendar"}
        words = parsed.path.split("/")
        for word in words:
            word = word.lower()
            if word in bad_words:
                return False
            elif word.isdigit() and len(word) == 4: ## double check this to maybe restrict to a certain date
                return False
        
        #grape.ics.edu, doku.php, version=,
        if '/machine-learning-databases' in parsed.path:
            return False
        elif '/dataset' in parsed.path:
            return False
        elif '/people' in parsed.path: #fixes denied by robot rules 608 error for lots of links
            return False
        elif "tab_details=" in parsed.query: #ensures unique and useful urls by stripping repetitive queries
            return False
        elif "tab_files=" in parsed.query:
            return False
        elif "action=" in parsed.query:
            return False
        elif "do=" in parsed.query:
            return False
        elif "diff=" in parsed.query:
            return False
        elif "version=" in parsed.query:
            return False
            
        
        #trap checks
        #went down from bigger numbers like 500 and 10 and tested downwards
        if len(url) > 200 or len(parsed.query)>100:
            return False
         
        depth_count = parsed.path.count('/') 
        if depth_count > 8: 
            return False

       
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
            

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def is_exact_duplicate(content: bytes) -> bool:
    #use checksum to check exact duplicate
    #use checksum to basically store in a set the number of bytes per page and compare based on that
    M = 2 ** 32 #standard word size in networking operations
    checksum_value = 0
    for byte in content:
        checksum_value += byte 

    checksum_value %= M

    if checksum_value in seen_checksums:
        return True
    else:
        seen_checksums.add(checksum_value)
        return False

def get_words(string: str) -> set[str]:
    words = set()
    curr = ""

    #used in in_near_duplicates
    #unique words in the string for later comparison
    for char in string:
        if char.isalnum():
            curr += char
        else:
            if len(curr) != 0:
                words.add(curr)
            curr = ""
    
    #accounts for last word in string
    if len(curr) != 0:
        words.add(curr)
    
    return words

def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    #find the intersection or common words they have
    inter = 0
    for word2 in set2:
        if word2 in set1:
            inter += 1

    #compute the union using basic probability rule
    union = len(set1) + len(set2) - inter
    #prevent zero error
    if union != 0:
        return inter / union
    else:
        return 1.0


def is_near_duplicate(content: bytes) -> bool:
    #check for near duplicates using jaccard_similarity
    #call helper function
    words_set = get_words(content.decode("utf-8", errors="ignore"))

    #compare similarity of all the seen urls
    for seen_doc in seen_docs:
        sim = jaccard_similarity(words_set, seen_doc)
        #changed from 0.9
        if sim > 0.85:
            return True
    
    seen_docs.append(words_set)
    return False
