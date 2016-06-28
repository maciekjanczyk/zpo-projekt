# VirtManager - wersja 0.1a
autor: janczyk@linux.pl

Jest to projekt wykonany na zaliczenie przedmiotu "Zaawansowane programowanie obiektowe" na kierunku "Informatyka Stosowana" (UMK Toruń). VirtManager stanowi platformę do zarządzania maszynami wirtualnymi VirtualBox dla wielu użytkowników. Na platofmę składa się

  - RestAPI - dostępne pod prefiksem /api/ aplikacji
  - Serwisu Web z bazą danych użytkowników

Oto możliwości zarządzania jakie daje platforma:

   - tworzenie nowych maszyn
   - usuwanie maszyn
   - zmiana naw maszyn
   - włączenie maszyny wirtualnej
   - wykonywanie zrzutów ekranu
   - wykonywanie zrzutów ekranu w formie wideo
   - dostęp do terminala z poziomu aplikacji web

Każdy z użytkowników ma na głównym serwerze grupę maszyn nazwane ich nickami. Instalacja nowej maszyny polega na skolonowaniu wzorca który należy do grupy "distros", który ma zainstalowany tzw. guest additions


### Wersja
0.1a

### Tech

Użyte technologie:

* [Python] - najlepszy skryptowy język programowania
* [pyvbox] - jedyna biblioteka do API VirtualBoxa dla Pythona
* [CherryPy] - doskonały framework do budowania aplikacji webowych
* [Bootstrap] - zestaw przydatnych narzędzi ułatwiających tworzenie interfejsu graficznego stron oraz aplikacji internetowych
* [jQuery] - doskonale znana biblioteka

### Instalacja

Jedyne co jest wymagane, to interpreter Pythona (2.7), dev kit dla VirtualBox oraz biblioteka pyvbox.

Zeby zainstalowac pyvbox:

```sh
$ pip install pyvbox
```

Stąd pobierzesz dev kit do VirtualBox:
http://download.virtualbox.org/virtualbox/3.2.12/VirtualBoxSDK-3.2.12-68302.zip

Domyślnie aplikacja uruchamia się na porcie 8081. Żeby to zmienić, wystarczy w pliku program.py edytować linię 327:

```py
conf = {
        'server.socket_port': 8081
    }
```

Na końcu uruchamiamy program:

```sh
$ python program.py
```


Licencja
----

MIT


