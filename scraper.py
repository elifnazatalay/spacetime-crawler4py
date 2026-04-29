import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

unique_pages = set()

def scraper(url, resp):
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
    hyperlinks = []
    if resp.status!=200:
        print(resp.error)
        return hyperlinks
    elif resp.raw_response==None or not resp.raw_response.content:
        return hyperlinks

    defrag, _ = urldefrag(url)
    unique_pages.add(defrag)
    with open('report.txt', 'w') as f:
        pages = str(len(unique_pages))
        f.write(f"Final unique number of pages: {pages}")
        

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    for link in soup.find_all('a', href=True):
        joined = urljoin(url, link['href'])
        joined, _ = urldefrag(joined)
        hyperlinks.append(joined)

    return hyperlinks

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    #remove calenders and ML sites
    try:
        ## normalize case
        parsed = urlparse(url.lower())
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        ## contains //
        if "//" in url:
            return False

        domains = {
            'ics.uci.edu',
            'cs.uci.edu', 
            'informatics.uci.edu',
            'stat.uci.edu'
        }
        if not any(parsed.netloc.endswith(d) for d in domains):
            return False
        
        ## strip off fragment
        parsed = parsed._replace(fragment = "")
        parsed = urlparse(url)

        ## query parameters
        if parsed.query != "":
            return False
        
        ## invalid keywords
        words = parsed.path.split("/")
        for word in words:
            if word == "signup" or word == "logout" or word == "login" or word == "mailto" or word == "register" or word == "javascript":
                return False
        
        ## calendar / dynamic pages
        for word in words:
            if word == "calendar" or word == "archive" or word == "event":
                return False
            if word.isdigit() and len(word) > 4: ## duoble check this
                return False
            
        ## ml sites
        ml_words = {"ml", "machine-learning", "deep_learning", "machine_learning", "deep-learning", "tensorflow", "neural",  "ai", "pytorch"}
        for word in words:
            if word in ml_words:
                return False
            
        
        ## length of path
        if len(url) > 300:
            return False
         
        ## depth of path
        depth_count = parsed.path.count('/')
        if depth_count > 6: ## path always starts with /
            return False
       

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
    
        ## repeated patterns, double check this
        # duplicate_count = 0
        # prev_word = None
        # for word in words:
        #     if word != "" and word == prev_word:
        #         duplicate_count += 1
        #         if duplicate_count > 2:
        #             return False
        #     prev_word = word
        non_empty_words = [w for w in words if w != ""]
        for k in range(1, 4):
            pattern = non_empty_words[0:k]
            if pattern != "" and len(non_empty_words) > k * 2:
                if all(non_empty_words[i:i+k] == pattern for i in range(0, len(non_empty_words), k)):
                    return False
    
        return True
    

    except TypeError:
        print ("TypeError for ", parsed)
        raise
