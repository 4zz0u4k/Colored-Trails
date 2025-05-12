from model.game_model import ColoredTrailsModel

if __name__ == "__main__":
    model = ColoredTrailsModel()
    model.running = True
    i = 1
    while model.running:
        print("[!] Starting itteration : ",i)
        model.step()
        print("[!] Ended itteration : ",i)