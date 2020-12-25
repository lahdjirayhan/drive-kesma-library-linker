# drive-kesma-library-linker

LINE bot to deliver links of e-books from HIMASTA-ITS Kesma Library straight through chat. Also, a helper to do my attendance (absensi) for me. Inherently a for-myself project.

# Introduction

I make this bot originally for personal use. I find it repetitively boring and distracting to do register my attendance (doing absensi) manually through my browser while also being engaged in Zoom class. Given that I use LINE and have a LINE app opened most of the time, I decided to make a bot that can do it easily for me.

My goal is to be able to make the bot go register my attendance just by telling the bot two things: the course (*mata kuliah*, MATKUL for short) and the attendance code (*kode presensi*).

If you're also interested in using this bot, you can add this bot as friend by its LINE ID `@573nveuh` or via https://line.me/R/ti/p/%40573nveuh

# Keywords

The bot will not respond to chats other than these keywords:

## `*auth`

Usage: `*auth`

What it does: Sends you a link that displays a "Sign In" page. The page is not a sign-in system in any way, it is just there so that you can enter your authorization detail more securely [1]. After you press "Sign In" there, your authorization detail will be remembered and associated with your LINE account. You can then subsequently use the bot to do presensi.

Whatever password you enter in the "Sign In" page will not be checked whether it's correct. If doing presensi using `!` (see below) results in a warning that say the login is unsuccessful, perhaps you have entered the wrong password. In such case, you can use `*auth` to enter the "Sign In" page again and update your password by entering the correct one.

Note: the login link can't be reused, but you can get another login link using `*auth` whenever you need.

## `*deauth`

Usage: `*deauth`

What it does: Removes/forgets the authorization detail previously associated with your LINE account.

## `!` (key absen identifier)

Usage: `!MATKUL KODE_PRESENSI`, e.g. `!ekon 123123`. No space between `!` and `MATKUL`.

What it does: Tells the bot to go filling your absensi. 

The bot fills your presensi by impersonating you, by using the authorization detail it has remembered from the usage of `*auth` [2]. The steps it takes are:

1. Go to https://presensi.its.ac.id
2. Login using authorization detail associated with your LINE account. If login fails/has wrong detail, terminate.
3. Infer the course that requires absensi:
    - Determine which course is the MATKUL keyword is pointing to. If appropriate course is found, select that course. Otherwise, declare MATKUL is not recognized and terminate.
    - Enter the selected course's page.
4. Infer the date that requires absensi:
    - Search for an entry that is marked with today's date, starting from latest schedule date to older schedule date. If found, select that entry. Otherwise,
    - Search for an entry that has its status ALPA, starting from latest schedule date to older schedule date. If found, select that entry. Otherwise,
    - Declare that no entry in the course's page is actionable and terminate.
5. Enter the KODE_PRESENSI in the selected entry.
6. Return the status: successful, failed, or already HADIR; and terminate.

# Notes

 - [1] Using the "Sign In" login page is more secure compared to previous implementation of sending `*auth USERNAME PASSWORD` over LINE chat (now deprecated, see commit history). That is because chats to official accounts **can't be unsent**. It can be deleted, but it has to be **deleted individually** on every device you are logged into (e.g. deleting it on your phone does not automatically deletes the chat history on your PC if you're logged in there, vice versa). It is a hassle and prone to be seen by people looking over your shoulder since the password (just like any other chats) will be displayed in cleartext (`PASSWORD` not `********`).

- [2] To summarize, the bot controls Selenium webdriver to impersonate a person using a browser to access a website. It takes steps like normal person doing absensi: logging in, selecting course, selecting entry on the provided schedule, and filling in the kode presensi. In order to do that, the bot will require username and password to go past the login page. However, note that your username and password is encrypted while being stored in the cloud database and can't be easily read or obtained.

 # Disclaimer
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.