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

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "if", "in",
    "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that", 
    "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "you", "your",
    "yours", "yourself", "yourselves"
}


def scraper(url, resp):
    
    #ensure no duplicate links within a crawl
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
    ##sunique_pages.add(defrag)

     ## write subdomain code here
    if defrag not in unique_pages:
        unique_pages.add(defrag)
        parsed = urlparse(url)
        net_loc = parsed.netloc
        # parts = net_loc.split(".")
        # sub_domain = ".".join(parts[0:len(parts)-2])

        if net_loc.endswith("uci.edu"):
            ##sub_domain = net_loc.replace(".uci.edu", "")
            if net_loc == "uci.edu":
                pass
            else:
                subdomain_count[net_loc] += 1
    
    if len(resp.raw_response.content) > 3_000_000:
        print("File too large to parse")
        return hyperlinks
    elif len(resp.raw_response.content)<30: #for too small of files
        return hyperlinks

    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    words = get_words_from_html(soup)
    word_count = len(words)

    filtered_words = []

    for word in words:
        if word not in STOP_WORDS and len(word) > 1:
            filtered_words.append(word)

    word_frequencies.update(filtered_words)

    if word_count > longest_page_word_count:
        longest_page_word_count = word_count
        longest_page_url = defrag
   

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
        elif "tab_details=" in parsed.query:
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
        elif "swiki" in parsed.netloc: #archived wiki and veryyy slow to download
            return False
            
        
        #trap checks
        if len(url) > 200. or len(parsed.query)>100:
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
