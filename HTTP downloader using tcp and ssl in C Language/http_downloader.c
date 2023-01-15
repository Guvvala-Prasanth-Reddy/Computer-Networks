#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include<arpa/inet.h>
#include<openssl/ssl.h>
#include<pthread.h>
#include <fcntl.h>

long long mutex_count = 0;
long long mutex_for_file_write= 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;



struct Arguments_for_thread_function{
    char* hst_name ;
    char* ip_address_destination ;
    char* destination_file_name ;
    SSL_CTX* ssl_ctx ;
    int i ;
    char* intermediate_request;
    int last_part_length ;
    int file_length;
};
struct Arguments_for_write_function{
    char* filename;
    char* buffer;
    int length;
    int part;
};

char* make_an_http_request(char* method , char* host_name , char* uri)
{


}
void write_files(char *filename , char* buffer , int part , int length)
{
  if( strstr(buffer , "HTTP/1.1 206 Partial Content") == NULL)
  {

  char file_no[20];
  sprintf(file_no , "%d_" , part);
  //FILE *fptr = fopen(strcat(filename , file_no) , "ab");
  FILE *fptr = fopen(strcat(file_no ,filename ) , "ab" );
  fwrite(buffer ,  1, length , fptr);
  fclose(fptr);
  printf("%s  mutex: %lld\n" , file_no , mutex_count );
}
}
void stitch_back_the_file(char *filename , int no_of_parts )
{
  printf("before seg0");
  FILE *fptr = fopen(filename , "ab");
  for(int i = 0 ; i < no_of_parts ; i++)
   {
     char file_no[20];
      sprintf(file_no , "%d_" , i);
  //   printf("before seg2");
      FILE *intermediate_file = fopen(strcat(file_no ,filename ) , "rb" );
      fseek(intermediate_file , 0 , SEEK_END);
      int size = ftell(intermediate_file);
      rewind(intermediate_file);
      char bytes[size];
      fread(bytes , sizeof(bytes) , 1 , intermediate_file);
      fwrite(bytes , sizeof(bytes) , 1 , fptr);
      fclose(intermediate_file);
    //   while(feof(intermediate_file))
    //   {
    //     byte = fgetc(intermediate_file);
    //      fputc(byte , fptr);
    //    }
    //    fclose(intermediate_file);
    // }
   }
   fclose(fptr);
}
void free_and_close()
{
  
}



char* get_ip_from_request(char* hst_name , char* ip_address_destination)
{
  int dns_result;
  struct addrinfo *dns_list;
  struct addrinfo *temp_itr;
  char ip_address_temp[NI_MAXHOST];

  dns_result = getaddrinfo(hst_name , "80" ,NULL, &dns_list );
  if( dns_result != 0)
  {
    fprintf(stderr,"DNS failed %s" , gai_strerror(dns_result));
  }
  
  for( temp_itr=dns_list ; temp_itr != NULL; temp_itr = temp_itr->ai_next)
  {
    printf( "---- Ip returned -----\n");
    
    int conv_flag = getnameinfo(temp_itr->ai_addr , temp_itr->ai_addrlen , ip_address_temp , NI_MAXHOST ,NULL , 0 , NI_NUMERICHOST );

    if( conv_flag )
    {
      fprintf(stderr , "error in getnameinfo() %s \n" , gai_strerror(conv_flag));
    }
    if( temp_itr->ai_family == AF_INET )
    {
      // memset(ip_address_temp , "\0" , sizeof(ip_address_temp));
      //printf("IPV4 : %s" , ip_address_temp);
      strcpy( ip_address_destination , ip_address_temp );
      break;
    }

    printf("address : %s\n" , ip_address_temp);


  }
  return ip_address_destination;

}
int process_http_response(char* buffer  )
{
  int Accept_ranges = 0;
  int content_length;
  char* ac_flag = strstr(buffer , "Accept-Ranges: bytes");
  char* cl_flag = strstr(buffer , "Content-Length: ");
  if( cl_flag == NULL)
  {
    cl_flag = strstr(buffer , "Content-length");
  }
  if( cl_flag == NULL)
  {
    cl_flag = strstr(buffer , "content-length");
  }
  if( cl_flag == NULL)
  {
    cl_flag = strstr(buffer , "content-Length");
  }
  if( ac_flag != NULL)
  {
    Accept_ranges = 1;
    printf("Ac flag exists\n");
    
  }
  if(cl_flag != NULL)
  {
    int i = 0;
    char content[20];
    cl_flag = cl_flag+16;
    char* end_flag = strstr(cl_flag , "\r\n");
    if( end_flag != NULL){
      i = strlen(cl_flag) - strlen(end_flag);
    }
    printf("%s" , cl_flag);
    strncpy(content , cl_flag , i);
    content_length = atoi(content);
  }
  
  return content_length;

}

int create_and_open_tcp_socket(char* ip_address_destination)
{
  int socket_number;
  socket_number = socket(AF_INET , SOCK_STREAM , 0);
  struct sockaddr_in destination_address;
  destination_address.sin_family = AF_INET;
  destination_address.sin_port = htons(443);
  destination_address.sin_addr.s_addr = inet_addr(ip_address_destination);

  int connection = connect(socket_number , (struct sockaddr *) &destination_address , sizeof(destination_address));
  if( connection == -1)
  {
    fprintf(stderr , "Connection failed %s \n" , gai_strerror(connection));
  }
  //  fcntl(socket_number, F_SETFL, O_NONBLOCK);
  return socket_number;
}
SSL* bind_socket_with_tls_session(char* hst_name , int socket_number , SSL_CTX* ssl_ctx)
{


  // create an SSL connection and attach it to the socket
  SSL *conn = SSL_new(ssl_ctx);

  SSL_set_tlsext_host_name(conn, hst_name);

  SSL_set_fd(conn,socket_number);


  // perform the SSL/TLS handshake with the server - when on the
  // server side, this would use SSL_accept()
  int err = SSL_connect(conn);
  if (err != 1)
  {
    printf("error in ssl\n");
    abort(); // handle error
}

printf("ssl connection succeeded\n");
return conn;
}
void* parallel_function( void* arguments )
{
    printf("please");
    printf("please 1");
    struct Arguments_for_thread_function* args = (struct Arguments_for_thread_function*) arguments;
    char* hst_name = args->hst_name;
    char* ip_address_destination = args->ip_address_destination ;
    char* destination_file_name = args->destination_file_name ;
    int i  = args->i;
    char* intermediate_request = args->intermediate_request;
    int last_part_length = args->last_part_length;
    SSL_library_init ();
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();
    SSL_CTX *ssl_ctx = SSL_CTX_new (SSLv23_client_method());

    int resp = 0;
    int prev = 0;
    char recur_buffer[last_part_length*2];
    char perm_buffer[args->file_length];
    int socket_number = create_and_open_tcp_socket(ip_address_destination);
    SSL *conn = bind_socket_with_tls_session(hst_name , socket_number , ssl_ctx);
    if( resp = SSL_write(conn , intermediate_request , strlen(intermediate_request)) < 0){ 
    perror("ERROR writing to ssl socket");
    }
    int k = 0;
    for (;;) {      
          printf("waiting for the response\n ---\n %s \n---\nvalue in the ssl buff %d\n" , recur_buffer, SSL_peek(conn , recur_buffer , last_part_length*2));
          explicit_bzero(recur_buffer, last_part_length);
          if ((resp = SSL_read(conn, recur_buffer, last_part_length*2)) < 0) {
              perror("ERROR reading from socket.");
              break;
          }
          if (!resp){
            printf("2");
            break;
          }
          else{
        // printf("%s length: %d\norder : %d", recur_buffer , strlen(recur_buffer) , k++);
         // printf("length : %d\n" , strlen(recur_buffer));
         if( strstr(recur_buffer , "HTTP/1.1 206 Partial Content") == NULL){
          //strncpy(&perm_buffer[k] , recur_buffer , resp);
          k += resp;
          write_files(destination_file_name , recur_buffer , i , resp);
            // strcat(perm_buffer , recur_buffer); 
         printf("bytes received %d\n" , resp);
         printf("%s\n" , recur_buffer);
         }
         else
         {
          char* offset = strstr(recur_buffer , "/r/n/r/n");
          if( offset != NULL)
          {
            offset = offset+4;
            k += strlen(offset);
            write_files(destination_file_name , recur_buffer + (resp-strlen(offset)), i , strlen(offset));
          }
         }
        if( k == last_part_length){
          SSL_free(conn);
          close(socket_number);
         break;}
          }
      printf("k == %d\n,Content : %slast_part_length: %d\n " ,k , recur_buffer, last_part_length);
}
printf("k = %d\n" , k);

// printf("%s \n" , perm_buffer);ur
// pthread_mutex_lock(&mutex);
// mutex_count--;
// pthread_mutex_unlock(&mutex);
}
 

void main(int argc, char **argv)
{
  char* https_link = NULL;
  char* destination_file_name = NULL;
  char* no_of_tcp_connections= NULL;

  
  char hst_name[64];
  char ip_address_destination[NI_MAXHOST];

  for(int i = 0 ; i < argc ; i++)
  {
    if( strcmp(*(argv+i) , "-u") == 0)
    {
      https_link = *(argv+i+1);
    }
    if( strcmp(*(argv+i) , "-o") == 0)
    {
      destination_file_name = *(argv+i+1);
    }
     if( strcmp(*(argv+i) , "-n") == 0)
    {
      no_of_tcp_connections = *(argv+i+1);
    }
  }
  char* path[1024];
  sscanf(https_link , "%*[^:]%*[:/]%[^/]%s", hst_name, path);
  printf("%s" , hst_name);
  strcpy(ip_address_destination , get_ip_from_request(hst_name , ip_address_destination));
  printf("arguments  %s %s %s \n",https_link, destination_file_name , no_of_tcp_connections );

  printf("Final destination ip %s\n" , ip_address_destination);
  int socket_number = create_and_open_tcp_socket(ip_address_destination);

  SSL_library_init ();
  SSL_load_error_strings();
  OpenSSL_add_ssl_algorithms();
  SSL_CTX *ssl_ctx = SSL_CTX_new (SSLv23_client_method());

  SSL *conn = bind_socket_with_tls_session(hst_name , socket_number , ssl_ctx);

  //forming an HEAD request from the arguments passed from the command line


  char intermediate_request[2048];
  sprintf(intermediate_request , "HEAD %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\nUser-Agent: PostmanRuntime/7.29.2\r\n\r\n" , path , hst_name);


  //char* request = "HEAD /~perdisci/CSCI6760-F21/Project2-TestFiles/story_hairydawg_UgaVII.jpg HTTP/1.1\r\nHost: cobweb.cs.uga.edu\r\n\r\n";
  char* request = intermediate_request;
  int resp = 0;
  printf("%s" , request);
  if( resp = SSL_write(conn , request , strlen(request)) < 0)
  {
    perror("ERROR writing to ssl socket");
  }
  char response_buffer[4096];
  char perm_buffer[4096];
  int content_length;
    for (;;) {
          explicit_bzero(response_buffer, 4096);
          if ((resp = SSL_read(conn, response_buffer, 4095)) < 0) {
              perror("ERROR reading from socket.");
              break;
          }
          if (!resp) break;
          printf("%s length: %d\n", response_buffer , strlen(response_buffer));
          content_length = process_http_response(response_buffer);
      }

  /* Experiementaton part */



  int no_of_tcp_connections_int = atoi(no_of_tcp_connections);
  int part_length = content_length/(no_of_tcp_connections_int);

  int last_part_length = part_length+content_length-(no_of_tcp_connections_int)*part_length;
  printf("last part length %d" , last_part_length);
  unsigned char recur_buffer[last_part_length];
  printf("no of tcp %d" , no_of_tcp_connections_int);
  pthread_t threads[no_of_tcp_connections_int];
  for(int i = 0 ; i < no_of_tcp_connections_int ; i++ )
  {
    
        printf("i %d\n" , i);

        if( i != no_of_tcp_connections_int-1)
        {
            sprintf(intermediate_request , "GET %s HTTP/1.1\r\nHost: %s\r\nRange: bytes=%d-%d\r\nUser-Agent: PostmanRuntime/7.29.2\r\n\r\n" , path , hst_name , i*part_length , (i+1)*part_length-1 ) ;
        }
        else
        {
            sprintf(intermediate_request , "GET %s HTTP/1.1\r\nHost: %s\r\nRange: bytes=%d-%d\r\nUser-Agent: PostmanRuntime/7.29.2\r\n\r\n" , path , hst_name , i*part_length , i*part_length + last_part_length-1 ) ;
        }
        printf("%s" , intermediate_request);
        struct Arguments_for_thread_function arguments;
        arguments.hst_name = hst_name;
        arguments.destination_file_name = destination_file_name;
        arguments.i = i;
        arguments.ip_address_destination = ip_address_destination;
        arguments.intermediate_request = intermediate_request;
        arguments.last_part_length = part_length;
        if( i == no_of_tcp_connections_int-1)
        {
          arguments.last_part_length = last_part_length;

        }
        arguments.ssl_ctx = ssl_ctx;
        arguments.file_length = content_length;

    //Critical section
    //       pthread_mutex_lock(&mutex);
    // mutex_count++;
    // pthread_mutex_unlock(&mutex);
    //end of critical section
        pthread_create(&threads[i] , NULL , parallel_function ,(void *) &arguments);
        pthread_join(threads[i] , NULL);
        //parallel_function(&arguments);
    }


    // while(mutex_count != 0)
    // {
    //    // printf("mutex_count :  %d \n" , mutex_count);
    // }
   stitch_back_the_file(destination_file_name , no_of_tcp_connections_int);


    SSL_free(conn);
    close(socket_number);
    SSL_CTX_free(ssl_ctx);

}