#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>
#include <limits.h>
//#include "Lepton_I2C.h" /* Change this to the C file */
#include <string.h>
#include <netdb.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define PORT 8888
#define BUFSIZE 512

/* Function Prototypes */
static void send_image(void);
int get_image();
int transfer(int fd);
void error(char *message);
void monitor(int signal);
static void save_numpy_file(void);

/* Program Variables */
static const char *device = "/dev/spidev0.1";
static uint8_t mode;
static uint8_t bits = 8;
static uint32_t speed = 16000000;
static uint16_t delay;

#define VOSPI_FRAME_SIZE (164)
uint8_t lepton_frame_packet[VOSPI_FRAME_SIZE];

static unsigned int image_data[60][80];

int main(int argc, char **argv)
{
	struct sockaddr_in myaddr; /* our address */ 
    struct sockaddr_in remaddr; /* remote address */ 
    socklen_t addrlen = sizeof(remaddr); /* length of addresses */ 
    int recvlen; /* # bytes received */ 
    int fd; /* our socket */ 
    unsigned char buf[BUFSIZE]; /* receive buffer */

	if ((fd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) 
	{ 
		error("cannot create socket\n"); 
		return 0; 
	}

	memset((char *)&myaddr, 0, sizeof(myaddr)); 
	myaddr.sin_family = AF_INET; 
	myaddr.sin_addr.s_addr = htonl(INADDR_ANY); 
	myaddr.sin_port = htons(PORT);

	if (bind(fd, (struct sockaddr *)&myaddr, sizeof(myaddr)) < 0) 
	{ 
		error("bind failed"); 
		return 0; 
	}

	int sent = 0;

    for (;;)
    {
    	printf("waiting on port %d\n", PORT); 

    	recvlen = recvfrom(fd, buf, BUFSIZE, 0, (struct sockaddr *)&remaddr, &addrlen); 
    	printf("received %d bytes\n", recvlen); 

    	if (recvlen > 0) 
    	{ 
    		buf[recvlen] = 0; 
    		printf("received message: \"%s\"\n", buf); 

    		/* Stream the data!!! */
    		for (;;)
    		{

	    		if (get_image() == 1)
				{
					printf("Data from camera received\n");
					//save_numpy_file();

					sent = sendto(fd, image_data, sizeof(unsigned int) * 60 * 80, 0, (struct sockaddr *)&remaddr, addrlen);
					printf("Sent: %d\n", sent);
				}
				else
				{
					printf("couldn't get camera data\n");
				}

				usleep(80000);

			}

    	}
    	
	}
}

int get_image()
{
	int ret = 0;
	int fd;

	/* Open the FLIR lepton */
	fd = open(device, O_RDWR);

	/* Check for errors */
	if (fd < 0)
	{
		/* Do something here */
	}

	/* Do I need to do this every time??? or can i just initialize it at the start ??? */
	ret = ioctl(fd, SPI_IOC_RD_MODE, &mode);

	ret = ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits);

	ret = ioctl(fd, SPI_IOC_RD_BITS_PER_WORD, &bits);

	ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);

	ret = ioctl(fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);

	int discardedpackets = 0;

	while(transfer(fd) != 59)
	{
		if (discardedpackets > 1000)
		{
			discardedpackets = 0;
			return 0;
		}

		discardedpackets++;
	}

	close(fd);

	return 1;
}

int transfer(int fd)
{
	int ret;
	int i;
	int frame_number;
	int discardpackets = 0;

	uint8_t tx[VOSPI_FRAME_SIZE] = {0, };

	struct spi_ioc_transfer tr;
	memset((void *)&tr, 0, sizeof(struct spi_ioc_transfer));
	tr.tx_buf = (unsigned long)tx;
	tr.rx_buf = (unsigned long)lepton_frame_packet;
	tr.len = VOSPI_FRAME_SIZE;
	tr.delay_usecs = delay;
	tr.speed_hz = speed;
	tr.bits_per_word = bits;

	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);

	if (ret < 1)
		printf("can't send spi message\n");

	if(((lepton_frame_packet[0]&0xf) != 0x0f))
	{
		frame_number = lepton_frame_packet[1];

		if(frame_number < 60 )
		{
			for(i=0;i<80;i++)
			{
				image_data[frame_number][i] = (lepton_frame_packet[2*i+4] << 8 | lepton_frame_packet[2*i+5]);
			}
		}
	}
	
	return frame_number;
}

void error(char *message) 
{
	
	perror(message);
	exit(1);

}