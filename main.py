"""
Thumbnail Generation using Producer-Consumer Pattern with Multiprocessing
"""

import os
import multiprocessing as mp
from PIL import Image
from pathlib import Path


def producer_process(queue, producer_dir, thumbnail_size=(200, 200)):
    """
    Producer: Reads images, creates thumbnails, and puts them in queue

    Args:
        queue: Multiprocessing queue for communication
        producer_dir: Directory containing original images
        thumbnail_size: Size of thumbnail (width, height)
    """
    print(f"[Producer] Starting... Reading from '{producer_dir}'")

    # Get all image files from producer directory
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    image_files = []

    for filename in os.listdir(producer_dir):
        if filename.lower().endswith(image_extensions):
            image_files.append(filename)

    print(f"[Producer] Found {len(image_files)} images to process")

    processed_count = 0

    # Process each image
    for filename in image_files:
        try:
            # Full path to the image
            image_path = os.path.join(producer_dir, filename)

            # Open and create thumbnail
            with Image.open(image_path) as img:
                # Create a copy and resize it
                img_copy = img.copy()

                # Convert RGBA or other modes to RGB for JPEG compatibility
                if img_copy.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    rgb_img = Image.new('RGB', img_copy.size, (255, 255, 255))
                    # Paste the image on white background
                    if img_copy.mode == 'P':
                        img_copy = img_copy.convert('RGBA')
                    rgb_img.paste(img_copy, mask=img_copy.split()[-1] if img_copy.mode in ('RGBA', 'LA') else None)
                    img_copy = rgb_img
                elif img_copy.mode != 'RGB':
                    img_copy = img_copy.convert('RGB')

                img_copy.thumbnail(thumbnail_size, Image.LANCZOS)

                # Put thumbnail and filename in queue
                queue.put((filename, img_copy))
                processed_count += 1
                print(f"[Producer] Processed: {filename}")

        except Exception as e:
            print(f"[Producer] Error processing {filename}: {e}")

    # Send termination signal to consumer
    queue.put(None)
    print(f"[Producer] Finished! Processed {processed_count} images")


def consumer_process(queue, consumer_dir):
    """
    Consumer: Reads thumbnails from queue and saves them to disk

    Args:
        queue: Multiprocessing queue for communication
        consumer_dir: Directory to save thumbnails
    """
    print(f"[Consumer] Starting... Saving to '{consumer_dir}'")

    # Create consumer directory if it doesn't exist
    os.makedirs(consumer_dir, exist_ok=True)

    saved_count = 0

    # Keep consuming until termination signal (None) is received
    while True:
        # Get item from queue
        item = queue.get()

        # Check for termination signal
        if item is None:
            print(f"[Consumer] Received termination signal")
            break

        # Unpack the data
        filename, thumbnail = item

        try:
            # Create new filename with "-thumbnail" suffix
            name_without_ext = os.path.splitext(filename)[0]
            new_filename = f"{name_without_ext}-thumbnail.jpg"

            # Full path to save the thumbnail
            save_path = os.path.join(consumer_dir, new_filename)

            # Save the thumbnail
            thumbnail.save(save_path, 'JPEG')
            saved_count += 1
            print(f"[Consumer] Saved: {new_filename}")

        except Exception as e:
            print(f"[Consumer] Error saving {filename}: {e}")

    print(f"[Consumer] Finished! Saved {saved_count} thumbnails")
    return saved_count


def main():
    """
    Main function to orchestrate producer and consumer processes
    """
    # Define directories
    producer_dir = "producer"
    consumer_dir = "consumer"

    # Create directories if they don't exist
    os.makedirs(producer_dir, exist_ok=True)
    os.makedirs(consumer_dir, exist_ok=True)

    print("=" * 60)
    print("Thumbnail Preparation")
    print("=" * 60)

    # Create a multiprocessing queue for communication
    queue = mp.Queue()

    # Create producer process
    producer = mp.Process(
        target=producer_process,
        args=(queue, producer_dir)
    )

    # Create consumer process
    consumer = mp.Process(
        target=consumer_process,
        args=(queue, consumer_dir)
    )

    # Start both processes
    print("\n[Main] Starting processes...")
    producer.start()
    consumer.start()

    # Wait for both processes to complete
    print("[Main] Waiting for processes to complete...\n")
    producer.join()
    consumer.join()

    print("\n" + "=" * 60)
    print("[Main] All processes completed successfully!")
    print("=" * 60)

    # Count successful conversions
    thumbnail_count = len([f for f in os.listdir(consumer_dir)
                          if f.endswith('-thumbnail.jpg')])

    print(f"\n✓ Total images converted successfully: {thumbnail_count}")
    print(f"✓ Thumbnails saved in: {consumer_dir}/")


if __name__ == "__main__":
    main()
