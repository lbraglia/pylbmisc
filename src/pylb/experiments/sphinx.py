def basicrst(arg1, arg2):
    """
    Funzione per uso personale

    =============
    Formattazione
    =============
    
    Primo paragrafo.

    Secondo paragrafo con elenco e testo:
    1. primo elemento elenco numerato *corsivo*;
    2. secondo elemento elenco numerato **grassetto**:
       * sottoelenco puntato 1 
       * sottoelenco puntato 2
    3. codice ``print(100)``

    .. Questo è un commento.

    

    Titolo
    =====

    Sezione
    -------

    sottosezione
    ~~~~~~~~~~

    Link
    ====

    `Link a una pagina <https://domain.invalid/>`_

    Se un link deve essere ripetuto `google`_ e `google`_ conveiene
    definirlo una volta sola.
    
    .. _google: https://google.it/

    ========
    Funzioni
    ========

    :param arg1: primo argomento 
    :param arg2: secondo argomento **grassetto*.

    :returns: sum of two elements passed

    Example::

       sphinxexp1(1, 2)
       sphinxexp1(2, 3)       
       
    
    >>> sphinxexp1(1, 2)
    3

    """
    return arg1 + arg2
