import argparse
import csv
import logging

from run import db

FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


def insert_ds(src=None, dest=None):
    if src is None or dest is None:
        raise ValueError(f"src: {src}, dest: {dest}")
    with open(src) as fr:
        reader = csv.reader(fr)
        # skip header
        next(reader)
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            for row in reader:
                if len(row) != 2:
                    raise ValueError(f"Invalid row data: {row}")
                conn.execute(f'INSERT INTO "{dest}" (item_1,item_2) VALUES (?, ?)', row)
        except Exception as e:
            logger.exception(e)
            trans.rollback()
        else:
            trans.commit()
        finally:
            conn.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--unlabeled_dataset_csv", required=True, help="Path to unlabeled dataset csv"
    )
    parser.add_argument(
        "--unlabeled_dataset_table",
        default="unlabeled_dataset",
        help="Destination unlabeled dataset table",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    insert_ds(src=args.unlabeled_dataset_csv, dest=args.unlabeled_dataset_table)
