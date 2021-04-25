# drive-kesma-library-linker

LINE bot to do useful things for me as a student. Making repetitive, resource-intensive tasks, doable by just a simple chat command to a bot.

Project is inherently built with for-myself attitude but with best attempts at conforming to good practices in its development.

If you're interested in using this bot, you can add this bot as friend by its LINE ID `@573nveuh` or via https://line.me/R/ti/p/%40573nveuh. The LINE OA is named 'Goddard Space Center', after [this building in a game](https://cnc.fandom.com/wiki/Goddard_Space_Center) (not to be confused with [this actual spaceflight facility](https://www.nasa.gov/goddard/)).

Why I build this thing? [0]
# Functionalities

The bot has three capabilities at the time, doable via simple LINE chat:

- `(drive-linker)` Deliver direct download links of e-books and past exam test sheets that are stored in HIMASTA-ITS Kesma Library cloud storage.
- `(attendance-recorder)` Record class attendance through campus web portal.
- `(zoom-link-finder)` Find zoom link for class through campus web portal.

Because some of those capabilities i.e `(attendance-recorder)` and `(zoom-link-finder)` requires valid credential to go past campus web login portal, the bot also has one additional capability:

- `(auth)` Remember your login credentials and associate it with your LINE account.

# Keywords

The bot will only respond to certain key identifiers (characters/words). It will ignore all chats, except:

## `*auth`

Usage: `*auth`

What it does: Sends you a link that displays a page titled "Sign In". The said page is just a way for the bot to ask for your credentials [1]. It does not check whether the given credentials are correct. It merely remembers the given credentials and associates them with your LINE account (i.e. the LINE account that asked for `*auth` beforehand).

If you always get a login failed chat on using bot's capability that requires valid credentials i.e. `(attendance-recorder)`, it may be an indication that the bot remembers an invalid or wrong credential detail.

The bot needs your valid credentials to go through campus web portal's sign-in page. The credentials provided are used when necessary, i.e. by `(attendance-recorder)`. I acknowledge that storing credentials in a database is a security weakness. However, I'd like to note that while they're stored in a cloud database, they're encrypted.

Note: each login link is for one-time use only. If you need another login link (i.e. to make correction for your previously wrong password, or to update the bot when you change your password in campus website), you can use `*auth` again to request another login link. The credentials entered in the next login link will overwrite any credentials previously associated with your LINE account.

## `*deauth`

Usage: `*deauth`

What it does: Removes/forgets the authorization detail previously associated with your LINE account.

## `!` (Identifier to trigger `attendance-recorder`)

Usage: `!COURSE_NAME ATTENDANCE_CODE` without whitespace between `!` and `COURSE_NAME`. Example: `!ekon 123123` or `!ansur 999999`

What it does: Tells the bot to go recording attendance on course `COURSE_NAME` with code `ATTENDANCE_CODE`.

`COURSE_NAME` can be a full course name e.g. `statistika non parametrik`, or an abbreviation e.g. `statnonpar`. The bot does not support every possible course name or abbreviation. It has a pre-specified dictionary about these names and abbreviations.

If you're interested in adding support for other courses or adding new abbreviation to already existing course, you can contact me. Better yet, you are free to open a pull request to modify the pre-specified dictionary yourself [2]!

Specifics on the steps the bot takes to record attendance is specified here [3].


## `^` (Identifier to trigger `zoom-link-finder`)

Usage: `^COURSE_NAME`

What it does: Tells the bot to go login to online course portal and find the available zoom link for course `COURSE_NAME`.

`COURSE_NAME` can be a full course name e.g. `analisis multivariat`, or an abbreviation e.g. `multivar`. The bot does not support every possible course name or abbreviation. It has a pre-specified dictionary about these names and abbreviations.

## `ebook`

Usage:
- to display all available folders for e-books and their folder numbers: `ebook`
- to display certain course's e-book folder: `ebook FOLDER_NUMBER`

What it does:
- the `ebook` command gives you all subfolders and their 'folder numbers' (one for each course, usually) within Kesma Library's e-book folder. If you want to go to a specific course's folder, you need to remember its folder number given here.
- the `ebook FOLDER_NUMBER` command gives you direct download links for a specific course's e-books. `FOLDER_NUMBER` must be taken from what the `ebook` command gave previously.

Example of use:

You want to get download links for e-books of the course 'Data Mining'. First, you'll need to send the bot `ebook`. The bot will reply with all available coursea' subfolders with their folder numbers. Take note what number is 'Data Mining' associated with. Say it's associated with the number `1. Data Mining` then you can send `ebook 1` to get download links for 'Data Mining' course.
## `soal`

Usage:
- to display all available folders for past tests and their folder numbers: `soal`
- to display certain course's past tests folder: `soal FOLDER_NUMBER`

What it does:
- the `soal` command gives you all subfolders and their 'folder numbers' (one for each course, usually) within Kesma Library's bank soal folder. If you want to go to a specific course's folder, you need to remember its folder number given here.
- the `soal FOLDER_NUMBER` command gives you direct download links for a specific course's past tests. `FOLDER_NUMBER` must be taken from what the `soal` command gave previously.

Example of use:

You want to get download links for past tests of the course 'Data Mining Statistika'. First, you'll need to send the bot `soal`. The bot will reply with all subfolders with their folder numbers. Take note what number is 'Data Mining Statistika' associated with. Say it's associated with the number `25. Data Mining Statistika` then you can send `soal 25` to get download links for 'Data Mining Statistika' course.

Why don't I support pre-specified course codes instead for `(drive-linker)` i.e. `ebook` and `soal`? Look here [4].
# Notes

- [0] I make this bot because I'm bored and I'm learning Python. Why this bot? Because I find recording attendance is very repetitive but resourse-intensive, i.e. opening a browser while in the middle of Zoom class. Imagine the CPU and network usage on that occasion (makes my computer super *slow* not to mention *lagging* or even *crashing* either browser or Zoom), and at the same time my attention is getting divided into two different things at once. Over time I add more useful things that I can think of.

- [1] Using this "Sign In" login page is the more secure way of telling the bot about your credentials compared to easiest/most obvious methods, for example sending `*auth USERNAME PASSWORD` over LINE chat. That is because chats to official accounts (and therefore this bot also) **can't be unsent**. It can be deleted, but it has to be **deleted individually** on every device you are logged into (e.g. deleting it on your phone does not automatically deletes the chat history on your PC if you're logged in there, vice versa). It is a hassle and prone to be seen by people looking over your shoulder since the password (just like any other chats) will be displayed permanently in chat in cleartext (`PASSWORD` not `********`).

- [2] The file that contains the definition pre-specified dictionary for `(attendance-recorder)` and `(zoom-finder)` is in **`application/utils/course.py`**. See it for yourself for what courses are available and what abbreviations are supported.

- [3] The steps it takes are basically using a headless browser to impersonate an actual person doing the same thing:

    1. Go to https://presensi.its.ac.id
    2. Login using authorization detail associated with your LINE account. If login fails/has wrong detail, terminate.
    3. Infer the course that requires absensi:
        - Determine which course is the `COURSE_NAME` keyword is pointing to. If appropriate course is found, select that course. Otherwise, declare `COURSE_NAME` is not recognized and terminate.
        - Enter the selected course's timetable page.
    4. Infer the timetable entry that requires attendance recording:
        - Search for an entry that is marked with today's date, starting from most recent to oldest. If found, select that entry. Otherwise,
        - Search for an entry that has its status ALPA, starting from most recent to oldest. If found, select that entry. Otherwise,
        - Declare that no entry in the course's page is actionable and terminate.
    5. Enter the `ATTENDANCE_CODE` in the selected entry.
    6. Return the status: successful, failed, or already HADIR; and terminate.

- [4] I decide to not implement pre-specified dictionary for `(drive-linker)`. This is because Kesma Library is super messy, poorly maintained, and not neatly organized.
    * One course can have two different subfolders. Example: `Statmat` and `Stat Mat`. Which folder to choose, in this case?
    - Inconsistent numbering schemes for courses with multiple levels. Example: `Fisika 1` and `Fisika II`. One is Arabic numeral, the other is Roman numeral. While not actually impeding any coding implementation, this is a bad sign about Kesma Library's organization.
    * The E-book folder and Past Exams folder can have different names for one course, e.g. `Matematika IV` in E-book folder, but `Mat 4` in Past Exams folder.
    - Courses are not grouped by their current situation e.g. courses `Aljabar Linier I` and `Aljabar Linier II` both existed in 2013 curriculum, but are now merged into single course `Matriks` in 2018 curriculum. All three folders for each of them exist.
    * General lack of consistency in maintenance:
        - Entire 2018/2019 academic year sees **no update** at all to bank soal folder, which is supposed to be partially updated each semester and fully updated each year. Exams always exist and each semester results in fresh ones so I don't see any other reason.
        - I suspect (and sort of expect, actually) that Kesma Library directory will be unstable and changing to an unexpected but equally untidy file organization.

    Because of the aforementioned problems, I decide to just use folder numbering scheme to mirror the actual directory of Kesma Library cloud storage. However, if opportunity arises, I may attempt a design to work around all reasons I mentioned.
 # Disclaimer
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

I would like to also repeat that this project is made with for-myself attitude while also attempting my best to conform to best practices whenever possible.
