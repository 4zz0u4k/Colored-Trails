from model.game_model import ColoredTrailsModel

if __name__ == "__main__":
    model = ColoredTrailsModel()
    model.running = True
    while model.running:
        model.step()