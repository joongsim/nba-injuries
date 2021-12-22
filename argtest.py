import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", action='store_true')
    parser.add_argument("-p","--player", help="update players", action='store_true')
    args = parser.parse_args()
    
    if args.verbosity:
        print('verbosity turned on')
    
    if args.player:
        print('updating players')