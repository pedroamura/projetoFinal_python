    if email_professor:
        corpo = (
            f"Olá Prof. {nome_professor},\n\n"
            f"A sua reserva foi efetuada com sucesso!\n\n"
            f"• Laboratório: {laboratorio}\n"
            f"• Dia da semana: {dia}\n"
            f"• Data: {data_desejada_str}\n"
            f"• Horário: {horario}\n\n"
            f"Caso precise cancelar, utilize a sua matrícula no sistema."
        )
        disparar_email("Confirmação de Reserva de Laboratório", email_professor, corpo)