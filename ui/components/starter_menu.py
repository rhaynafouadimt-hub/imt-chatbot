import chainlit as cl


def get_starters():
    return [
        cl.Starter(
            label="Formations IMT",
            message="Quelles sont les formations proposées par l’IMT ?",
            icon="/public/images/ico_formation.png",
        ),
        cl.Starter(
            label="Frais de scolarité",
            message="Quels sont les frais de scolarité à l’IMT ?",
            icon="/public/images/frais.png",
        ),
        cl.Starter(
            label="Localisation",
            message="Où se situe l’Institut des Métiers du Tertiaire ?",
            icon="/public/images/loca.jpg",
        ),
        cl.Starter(
            label="Aide",
            message="Que peux-tu faire ?",
            icon="/public/images/aide.jpg",
        ),
    ]
