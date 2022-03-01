import sqlite3


class Database:

    def __init__(self,DB_LOCATION):
        self.connection = sqlite3.connect(DB_LOCATION)
        self.cur = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        self.cur.close()
        if isinstance(exc_value, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()

    def chk_conn(self):
        try:
            self.connection.cursor()
            return True
        except Exception as ex:
            return False

    def close(self):
        self.connection.close()

    def execute(self, query):
        self.cur.execute(query)

    def insert_row_automobileit(self, table_name, values):
        # pass None for null values
        self.cur.execute('''INSERT INTO {} (prezzo, colore_esterno, metallizzato, design_interni, colore_interni,
         in_grado_di_viaggiare, proprietari_precedenti, scadenza_revisione, multimedia, sicurezza, comfort,
          varie, luci, trasporto, assetto, consumo_combinato, consumo_extraurbano, consumo_urbano,
           emissioni_co2, classe_emissioni, tipologia, marca, modello, versione, carburante, chilometri,
            immatricolazione, potenza, cambio, numero_di_porte, numero_di_posti, cilindrata, carrozzeria,
             climatizzatore, filtro_antiparticolato, iva_deducibile, scraping_date)
         VALUES {},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}'''.format(table_name, values[0],
                                                                                         values[1],
                                                                                         values[2], values[3],
                                                                                         values[4], values[5],
                                                                                         values[6], values[7],
                                                                                         values[8], values[9],
                                                                                         values[10], values[11],
                                                                                         values[12], values[13],
                                                                                         values[14], values[15],
                                                                                         values[16], values[17],
                                                                                         values[18], values[19],
                                                                                         values[20], values[21],
                                                                                         values[22],
                                                                                         values[23], values[24],
                                                                                         values[25], values[26],
                                                                                         values[27], values[28],
                                                                                         values[29], values[30],
                                                                                         values[31], values[32],
                                                                                         values[33], values[34],
                                                                                         values[35],values[36],values[37]))

    def create_table_data(self, name):
        # 21 colonne
        self.cur.execute('''CREATE TABLE IF NOT EXISTS {}(offer_id varchar PRIMARY KEY, \
                                                                        prezzo int,
                                                                        colore_esterno varchar,
                                                                        metallizzato varchar,
                                                                        design_interni varchar,
                                                                        colore_interni varchar,
                                                                        in_grado_di_viaggiare varchar,
                                                                        immatricolazione varchar,
                                                                        proprietari_precedenti varchar,
                                                                        scadenza_revisione varchar,
                                                                        multimedia varchar,
                                                                        sicurezza varchar,
                                                                        comfort varchar,
                                                                        varie varchar,
                                                                        luci varchar,
                                                                        trasporto varchar,
                                                                        assetto varchar,
                                                                        consumo_combinato varchar,
                                                                        consumo_extraurbano varchar,
                                                                        consumo_urbano varchar,
                                                                        emissioni_co2 varchar,
                                                                        classe_emissioni varchar,
                                                                        tipologia varchar,
                                                                        marca varchar,
                                                                        modello varchar,
                                                                        versione varchar,
                                                                        carburante varchar,
                                                                        chilometri varchar,
                                                                        potenza varchar,
                                                                        cambio varchar,
                                                                        numero_di_porte varchar,
                                                                        numero_di_posti varchar,
                                                                        cilindrata varchar,
                                                                        carrozzeria varchar,
                                                                        climatizzatore varchar,
                                                                        filtro_antiparticolato varchar,
                                                                        iva_deducibile varchar,
                                                                        scraping_date varchar                                                                                                                        
                                                                        )'''.format(name))

    # adds column if not exist
    def add_column_to_table(self, table_name, column_name):
        for row in self.cur.execute('PRAGMA table_info({})'.format(table_name)):
            if row[1] == column_name:
                print('column {} already exists in {}'.format(column_name, table_name))
                break
        else:
            self.cur.execute('ALTER TABLE {} ADD COLUMN {} varchar'.format(table_name, column_name))
            print('added column {} to {}'.format(column_name, table_name))

    def commit(self):
        self.connection.commit()
