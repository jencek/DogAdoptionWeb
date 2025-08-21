import requests
from bs4 import BeautifulSoup
import json
import re



import os
import datetime
from urllib.parse import urlparse
from django.core.files.base import ContentFile
#from core.models import Dog  # adjust for your app name


import os
import requests
from urllib.parse import urlparse
from django.conf import settings



import argparse
import sys

image_dir = './media'



def download_image_to_field(model_instance, image_url, field_name='image'):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_name = os.path.basename(urlparse(image_url).path)
            getattr(model_instance, field_name).save(image_name, ContentFile(response.content), save=False)
    except Exception as e:
        print(f"Could not download image from {image_url}: {e}")





def download_image_to_media_folder(image_url, subfolder='dog_images'):
    try:
        image_name = os.path.basename(urlparse(image_url).path)
        #media_path = os.path.join(settings.MEDIA_ROOT, subfolder)
        media_path = os.path.join(image_dir, subfolder)
        #print(f"media_path:{media_path}")

        os.makedirs(media_path, exist_ok=True)

        full_file_path = os.path.join(media_path, image_name)

        # ✅ Skip if file already exists
        if os.path.exists(full_file_path):
            #print(f"⚠️ Skipping (already downloaded): {full_file_path}")
            return os.path.join(subfolder, image_name)

        # ⬇️ Download image content
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        with open(full_file_path, 'wb') as f:
            f.write(response.content)

        #print(f"✅ Saved image to {full_file_path}")
        return os.path.join(subfolder, image_name)

    except Exception as e:
        #print(f"❌ Failed to download image: {e}")
        return None





def extract_dog_data(n):
    base_url = "https://doggierescue.com/"
    #list_url = base_url + "dogs"
    #list_url = "https://doggierescue.com/search-pets/individual-dogs/?sf_paged=19"
    list_url = "https://doggierescue.com/search-pets/individual-dogs/?sf_paged="+str(n)
    

    #print ('processing page:'+str(n))
    response = requests.get(list_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    dogs = []

    dog_urls = set()

    # Look for dog image links and associated details: <a class="pp-post-link" href="https://doggierescue.com/dogs/alaska/" title="Alaska"></a>
    # https://doggierescue.com/search-pets/individual-dogs/?sf_paged=20
    for link in soup.select('a[href*="/dogs/"]'):
        href = link.get('href')
        #print(href)
        dog_url = base_url + href if not href.startswith('http') else href

        if dog_url in dog_urls:
            continue
        else:
            dog_urls.add(dog_url)


        # remove dupes


        try:
            dog_page = requests.get(dog_url)
            dog_page.raise_for_status()
            dog_soup = BeautifulSoup(dog_page.content, 'html.parser')

            # Extract details (name, breed, etc.)
            #print(dog_soup)
            #name = dog_soup.find('class','fl-heading-text')
            #print("dog_soup:" + str(dog_soup))
            #print(name)
            #name = dog_soup.find('font', {'size': '6'})

            url = dog_url
            dogid = url.rstrip('/').split('/')[-1]  # "venus-2"


            # get dog name
            #name = dogid.split('-')[0]  # "venus"
            name_sp = dog_soup.find('span', class_="fl-heading-text")
            if name_sp is not None:
                name = name_sp.get_text(strip=True)
                #print("name in page:"+name)
            else:
                name = dogid.split('-')[0]  # "venus"
                #print("name derived:"+name)



            sect_div = dog_soup.find_all('div', class_= "fl-col-content fl-node-content")
            #sect_div = dog_soup.find_all('div', class_= "fl-rich-text")
            for d in sect_div: 
                sp = d.find('span', class_="fl-heading-text")
                if sp:
                    #print(sp.get_text(strip=True)) 

                    if sp.get_text(strip=True) == 'Sex':
                        sex = d.find('div', class_="fl-rich-text").get_text(strip=True)
                        #print('sex:'+ sex)
                    elif sp.get_text(strip=True) == 'Breed':
                        breed = d.find('div', class_="fl-rich-text").get_text(strip=True)
                        #print('breed:'+breed)
                    elif sp.get_text(strip=True) == 'Age':
                        age = d.find('div', class_="fl-rich-text").get_text(strip=True)
                        #print('age:'+ age)
                    elif sp.get_text(strip=True) == 'Size':  
                        dsize = d.find('div', class_="fl-rich-text").get_text(strip=True)
                        #print('size:'+dsize)


            # Find the outer div
            # outer_div = dog_soup.find('div', class_='fl-rich-text')
            # print("outer_div")
            # print(outer_div)


            # Find Dog colours - do a prtial match on class name
            # print('****Find colour containers:')
            # par_list = dog_soup.find_all('div', class_=re.compile(r'\bfl-module fl-module-'))
            # for nd in par_list:
            #     print(nd)
            # print('***End Find colour contgainers:')
            


            # Find matching fl-module-heading or fl-module-rich-text with fl-node-*
            def match_partial_class(classes):
                if not classes:
                    return False
                comma_list = classes.split()
                cls = set(comma_list)
                #print("comma_list:")
                #print(comma_list)
                #print(cls)
                is_heading = {'fl-module', 'fl-module-heading'} <= cls and any(c.startswith('fl-node-') for c in comma_list)
                is_rich_text = {'fl-module', 'fl-module-rich-text'} <= cls and any(c.startswith('fl-node-') for c in comma_list)
                #print("is_heading:"+str(is_heading))
                #print("is_rich_text:"+str(is_rich_text))
                return is_heading or is_rich_text


            matches = dog_soup.find_all('div', class_=match_partial_class)
            #print('****Find colour containers:')
            useNextColour=False
            dog_colour=''
            
            useNextSize=False
            dog_size=''

            for nd in matches:
                ##print(nd)
                #print(nd.get_text(strip=True))
                if nd.get_text(strip=True) == 'Colours':
                    useNextColour=True
                    continue
                if useNextColour==True:
                    dog_colour=nd.get_text(strip=True) 
                    useNextColour=False
                    continue
 
                if nd.get_text(strip=True) == 'Size':
                    useNextSize=True
                    continue
                if useNextSize==True:
                    dog_size=nd.get_text(strip=True) 
                    useNextSize=False




            #print('****End colour containers:')

            # Then find the <p> tag inside it
            # dog details
            cont = dog_soup.find('span',class_="fl-post-info-terms")
            if  cont is None:
                details = []
            else:    
                details = cont.find_all('a')

            ditems = [d.get_text(strip=True) for d in details] if details else []
            #print(ditems)


            # get the dog image
            image_tag = dog_soup.find('div', class_='fl-photo-content fl-photo-img-jpg')
            if image_tag is None:
                image_tag = dog_soup.find('div', class_='fl-photo-content fl-photo-img-jpeg')
                #print('image_tag')
                #print(image_tag) 
 
            image_url = None
            if image_tag:
                img = image_tag.find('img')
                if img and img.has_attr('data-src'):
                    image_url = img['data-src']
                    #print('image_url:')
                    #print(image_url)
                    if image_url is not None:
                        target_url = download_image_to_media_folder(image_url, subfolder='dog_images')
                        #print(target_url)
                    else:
                        target_url - ""


            #
            # Get Notes for dog
            #
            notes = ""
            images_list = []
            gal = dog_soup.find('div',id="gallery")
            if gal:
                gal_notes = gal.find('div', class_='fl-rich-text')
                if gal_notes:
                    #print(gal_notes.get_text())
                    notes = gal_notes.get_text()

                gal_img = gal.find('div', class_='uabb-masonary')
                if gal_img:
                    imgs = gal_img.find_all('div', class_="uabb-photo-gallery-content uabb-photo-gallery-link")
                    if imgs:
                        for i in imgs:
                            #print('imgs iterator')
                            im = i.find('img',class_='uabb-gallery-img')
                            #print(im)
                            if im and im.has_attr('data-src'):
                                #print('has attr src')
                                gal_url = im['data-src']
                                #print(gal_url)
                                the_url = download_image_to_media_folder(gal_url, subfolder='dog_images')
                                images_list.append(the_url)


            dog_data = {
                'url': dog_url,
                'name': name,
                'nameext': dogid,
                'breed': breed,
                'sex': sex.title(),
                'age': age,
                'colour': dog_colour,
                'size': dog_size.title(),
                'notes': ', '.join(ditems)+"\n"+notes,
                'image': target_url,
                'images':images_list,
            }
            dogs.append(dog_data)
        except Exception as e:
            print(f"Failed to process {dog_url}: {e}")

    #return json.dumps(dogs, indent=2)
    return dogs





def parse_args():
    parser = argparse.ArgumentParser(description="Process file_out and log_file arguments.")
    
    # Required argument: file_out
    parser.add_argument(
        "--file_out", 
        required=True, 
        help="Path to the output file (required)"
    )
    
    # Optional argument: log_file
    parser.add_argument(
        "--log_file", 
        help="Path to the log file (optional)"
    )

    # Optional argument: log_file
    parser.add_argument(
        "--image_dir", 
        help="Path to the destination for image downloads. A dogs directory will be created under this dire (Optional. ./media )"
    )

    args = parser.parse_args()
    
    return args

def main():
    global image_dir

    args = parse_args()
    
    # Validation example (already handled by argparse, but shown explicitly)
    if not args.file_out:
        print("Error: --file_out is required.")
        sys.exit(1)
    
    print(f"Output will be written to: {args.file_out}")
    
    if args.log_file:
        print(f"Logging to: {args.log_file}")
    else:
        print("No log file provided.")

    if args.image_dir:
        print(f"Download images to: {args.image_dir}")
        image_dir = args.image_dir
    else:
        print(f"image_dir not provided. Download images to: ./media")


    dog_json = []
    for n in range(1,25):
        dog_json += extract_dog_data(n)
    
    with open(args.file_out, "w") as f:
        json.dump(dog_json, f, indent=2)


if __name__ == "__main__":
    main()



